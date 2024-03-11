# SPDX-FileCopyrightText: NOI Techpark <digital@noi.bz.it>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import absolute_import, annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from common.manager.traffic_station import TrafficStationManager
from pollution_connector.cache.computation_checkpoint import ComputationCheckpointCache, ComputationCheckpoint
from common.connector.collector import ConnectorCollector
from common.data_model.common import Provenance
from common.data_model.pollution import PollutionMeasure, PollutionMeasureCollection, PollutionEntry
from common.data_model import TrafficMeasureCollection, TrafficSensorStation
from pollution_connector.model.pollution_computation_model import PollutionComputationModel
from common.settings import DEFAULT_TIMEZONE, ODH_COMPUTATION_BATCH_SIZE

logger = logging.getLogger("pollution_connector.manager.pollution_computation")


class PollutionComputationManager(TrafficStationManager):

    def __init__(self, connector_collector: ConnectorCollector, provenance: Provenance, checkpoint_cache: Optional[ComputationCheckpointCache] = None):
        super().__init__(connector_collector, checkpoint_cache)
        self._provenance = provenance
        self._create_data_types = True

    @staticmethod
    def _compute_pollution_data(traffic_data: TrafficMeasureCollection) -> List[PollutionEntry]:
        """
        Compute the pollution data given the traffic data.

        :param traffic_data: The traffic data.
        :return: The pollution entries.
        """
        model = PollutionComputationModel()
        return model.compute_pollution_data(traffic_data)

    def _upload_pollution_data(self, pollution_entries: List[PollutionEntry]) -> None:  # If a data is already present it will be not overridden and data before the last measures are not accepted by the ODH
        """
        Upload the pollution data on ODH.

        :param pollution_entries: The pollution entries.
        """

        print(f"posting provenance {self._provenance}")
        if not self._provenance.provenance_id:
            self._provenance.provenance_id = self._connector_collector.pollution.post_provenance(self._provenance)

        print(f"posting data types {PollutionMeasure.get_pollution_data_types()}")
        if self._create_data_types:
            self._connector_collector.pollution.post_data_types(PollutionMeasure.get_pollution_data_types(), self._provenance)

        pollution_data = PollutionMeasureCollection.build_from_pollution_entries(pollution_entries, self._provenance)
        print(f"posting measures {len(pollution_data.measures)}")
        self._connector_collector.pollution.post_measures(pollution_data.measures)

    def run_computation_for_station(self,
                                    traffic_station: TrafficSensorStation,
                                    min_from_date: datetime,
                                    max_to_date: datetime):

        start_date = self._get_starting_date(self._connector_collector.pollution, traffic_station, min_from_date)

        # Detect inactive stations:
        # If we're about to request more than one window of measurements, do a check first if there even is any new data
        if (max_to_date - start_date).days > ODH_COMPUTATION_BATCH_SIZE:
            latest_measurement_date = self._get_latest_date(self._connector_collector.validation, traffic_station)
            # traffic data request range end is the latest measurement
            # For inactive stations, this latest measurement date will be < start_date, thus no further requests will be made
            # In general, it makes no sense to ask for data beyond the latest measurement, if we already know which date that is.
            logger.info(f"Station [{traffic_station.code}] has a large elaboration range. Latest measurement date: {latest_measurement_date}")
            max_to_date = min(max_to_date, latest_measurement_date)

        to_date = start_date

        if start_date < max_to_date:
            to_date = to_date + timedelta(days=ODH_COMPUTATION_BATCH_SIZE)
            if to_date > max_to_date:
                to_date = max_to_date

            logger.info(f"Computing pollution data for station [{traffic_station}] in interval [{start_date.isoformat()} - {to_date.isoformat()}]")

            traffic_data = []
            try:
                traffic_data = self._download_traffic_data(start_date, to_date, traffic_station)
            except Exception as e:
                logger.exception(
                    f"Unable to download traffic data for station [{traffic_station}] in the interval [{start_date.isoformat()}] - [{to_date.isoformat()}]",
                    exc_info=e)

            if traffic_data:
                try:
                    pollution_entries = self._compute_pollution_data(traffic_data)
                    self._upload_pollution_data(pollution_entries)
                except Exception as e:
                    logger.exception(f"Unable to compute data from station [{traffic_station}] in the interval [{start_date.isoformat()}] - [{to_date.isoformat()}]", exc_info=e)

                if self._checkpoint_cache is not None:
                    self._checkpoint_cache.set(
                        ComputationCheckpoint(
                            station_code=traffic_station.code,
                            checkpoint_dt=to_date
                        )
                    )

            start_date = to_date

    def run_computation_and_upload_results(self,
                                           min_from_date: datetime,
                                           max_to_date: datetime
                                           ) -> None:
        """
        Start the computation of a batch of pollution data measures. As starting date for the batch is used the latest
        pollution measure available on the ODH, if no pollution measures are available min_from_date is used.

        :param min_from_date: Traffic measures before this date are discarded if no pollution measures are available.
        :param max_to_date: Traffic measure after this date are discarded.
        """

        if min_from_date.tzinfo is None:
            min_from_date = DEFAULT_TIMEZONE.localize(min_from_date)

        if max_to_date.tzinfo is None:
            max_to_date = DEFAULT_TIMEZONE.localize(max_to_date)

        computation_start_dt = datetime.now()

        for traffic_station in self.get_traffic_stations_from_cache():
            self.run_computation_for_station(traffic_station, min_from_date, max_to_date)

        computation_end_dt = datetime.now()
        logger.info(f"Completed computation in [{(computation_end_dt - computation_start_dt).seconds}]")
