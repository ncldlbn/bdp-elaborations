// SPDX-FileCopyrightText: NOI Techpark <digital@noi.bz.it>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

package com.opendatahub.service;

import java.io.FileWriter;

import java.io.IOException;
import java.net.MalformedURLException;
import java.util.ArrayList;

import com.opendatahub.constantsClasses.Stop_Times;
import com.opendatahub.dto.Stop_TimesValues;

public class GTFSStop_Times {

	public static void writeStop_Times(ArrayList<Stop_TimesValues> stopTimesValues)
			throws IOException, MalformedURLException, GTFSCheckStopTimes {

		Stop_Times stoptimes = new Stop_Times();

		String firstLine = stoptimes.getTrip_id() + "," + stoptimes.getArrival_time() + ","
				+ stoptimes.getDeparture_time() + "," + stoptimes.getStop_id() + "," + stoptimes.getStop_sequence();

		GTFSReadFileFolder.readFiles();
		FileWriter writer = new FileWriter(GTFSReadFileFolder.getStop_Times());
		writer.write(firstLine);
		writer.write(System.getProperty("line.separator"));
		Stop_TimesValues stoptimesvalues = new Stop_TimesValues();
		if (GTFSCheckStopTimes.checkStopTimesMandatoryFields(stopTimesValues)) {
			for (int i = 0; i < stopTimesValues.size(); i++) {
				stoptimesvalues.setTrip_id(stopTimesValues.get(i).getTrip_id());
				stoptimesvalues.setArrival_time(stopTimesValues.get(i).getArrival_time());
				stoptimesvalues.setDeparture_time(stopTimesValues.get(i).getDeparture_time());
				stoptimesvalues.setStop_id(stopTimesValues.get(i).getStop_id());
				stoptimesvalues.setStop_sequence(stopTimesValues.get(i).getStop_sequence());
				writer.write(stoptimesvalues.getTrip_id() + ",");
				// well, not nice, but this solves the needed formatting of HH:MM:SS
				writer.write(stoptimesvalues.getArrival_time() + ":00" + ",");
				writer.write(stoptimesvalues.getDeparture_time() + ":00" + ",");
				writer.write(stoptimesvalues.getStop_id().toString() + ",");
				writer.write(String.valueOf(stoptimesvalues.getStop_sequence()));
				writer.write(System.getProperty("line.separator"));

			}
			writer.close();
		}
	}

	private static void writeStop_Times() {
		// TODO Auto-generated method stub

	}

	public static void main(String[] args) throws IOException {
		writeStop_Times();
	}

}
