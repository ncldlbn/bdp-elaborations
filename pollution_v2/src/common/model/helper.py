# SPDX-FileCopyrightText: NOI Techpark <digital@noi.bz.it>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
from typing import Iterable, List

import pandas as pd
import json
import logging

from common.data_model import TrafficSensorStation
from common.data_model.common import StationType
from common.data_model.history import HistoryEntry
from common.data_model.traffic import TrafficEntry

logger = logging.getLogger("pollution_v2.common.model")


class ModelHelper:

    @staticmethod
    def get_stations_dataframe(stations: dict[str, StationType]) -> pd.DataFrame:
        """
        Get a dataframe from the given list of traffic stations.
        The resulting dataframe will have the following columns:
        station,km

        :param stations: the stations
        :return: the station dataframe
        """
        temp = []
        for entry in stations.values():

            temp.append({
                "station_id": entry.id_stazione,
                "station_code": entry.code,
                "km": entry.km,
                "station_type": entry.station_type
            })

        return pd.DataFrame(temp)

    @staticmethod
    def get_traffic_dataframe(traffic_entries: Iterable[TrafficEntry]) -> pd.DataFrame:
        """
        Get a dataframe from the given traffic entries. The resulting dataframe will have the following columns:
        date,time,Location,Station,Lane,Category,Transits,Speed,km

        :param traffic_entries: the traffic entries
        :return: the traffic dataframe
        """
        temp = []
        for entry in traffic_entries:

            km = None
            if "a22_metadata" in entry.station.metadata:
                try:
                    meta: dict = json.loads(entry.station.metadata["a22_metadata"])
                    km = meta.get("metro")
                except Exception as e:
                    logger.warning(f"Unable to parse the KM data for station [{entry.station.code}], error [{e}]")

            temp.append({
                "date": entry.valid_time.date().isoformat(),
                "time": entry.valid_time.time().isoformat(),
                "Location": entry.station.id_strada,
                "Station": entry.station.id_stazione,
                "Lane": entry.station.id_corsia,
                "Category": entry.vehicle_class.value,
                "Transits": entry.nr_of_vehicles,
                "Speed": entry.average_speed,
                "Period": entry.period,
                "KM": km
            })

        return pd.DataFrame(temp)

    @staticmethod
    def get_traffic_dataframe_for_validation(traffic_entries: Iterable[TrafficEntry]) -> pd.DataFrame:
        """
        Get a dataframe from the given traffic entries. The resulting dataframe will have the following columns:
        time,value,station_code,variable

        :param traffic_entries: the traffic entries
        :return: the traffic dataframe
        """
        temp = []
        for entry in traffic_entries:

            temp.append({
                "time": entry.valid_time.time().isoformat(),
                "value": entry.nr_of_vehicles,
                "station_code": entry.station.code,
                "variable": entry.vehicle_class.value
            })

        return pd.DataFrame(temp)

    @staticmethod
    def get_history_dataframe(history_entries: Iterable[HistoryEntry]) -> pd.DataFrame:
        """
        Get a dataframe from the given history entries. The resulting dataframe will have the following columns:
        date,station_code,total_traffic

        :param history_entries: the history entries
        :return: the history dataframe
        """
        temp = []
        for entry in history_entries:

            temp.append({
                "date": entry.valid_time.date().isoformat(),
                "station_code": entry.valid_time.time().isoformat(),
                "total_traffic": entry.station.id_strada
            })

        return pd.DataFrame(temp)
