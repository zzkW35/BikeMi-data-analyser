from operator import itemgetter

import json
import re
import requests
import unidecode

class BikeMiApi:

    # Generate a list of stations, stored as dictionaries, starting from the 
    # json files provided by BikeMi at https://bikemi.com/dati-aperti/ 
    def jsonDecoder(self, InfoUrl):
        resp = requests.get(InfoUrl)
        raw = resp.json()
        # Pick the "stations" values inside the "data" key of the "raw" dict
        stations = raw['data']['stations']
        # Each station is a dictionary inside the list called "stations"    
        return(stations)

    # Get further info (bike availability) by scraping the website source
    def getStationsExtraInfo(self):
        raw = requests.get("https://bikemi.com/stazioni").text
        placeholder = '"stationMapPage","slug":null},'
        start = raw.find(placeholder) + len(placeholder)
        end = raw.find('"baseUrl":"https://bikemi.com"')
        stationExtraInfoRaw = raw[start:end].split('DockGroup:')
        # Each station is a string inside the list called "stationExtraInfo"
        stationExtraInfoList = []
        stationList = []
        del stationExtraInfoRaw[0]
        # Split the raw code into small chunks of data
        for station in stationExtraInfoRaw:
            station = station.split(",")
            data = [word for line in station for word in line.split(":")]

            # Create stationList list containing only the relevant data
            # Each station with its data is a list
            if len(data)==49:
                stationList.extend((data[1], data[2], data[5], data[6], 
                data[9], data[10], data[13], data[14], data[18],
                data[19], data[20], data[21], data[26], data[28],
                data[32], data[34], data[38], data[40]))

            if len(data)==50: # For the stations with extra address info
                stationList.extend((data[1], data[2], data[5], data[6],
                data[9], data[10], data[14], data[15], data[19], 
                data[20],  data[21], data[22], data[27], data[29], 
                data[33],  data[35],  data[39], data[41]))
            
            titles = stationList[::2] # Pick only the data placed in odd positions
            info = stationList[1::2] # Pick only the data placed in even positions

            # Data cleanup
            titles = [i.replace('"', '').replace('{', '') for i in titles]
            
            info = [i.replace('"', '').replace('}', '')
            .replace(']', '') for i in info]

            # Parse the data in a dictionary where "titles" are the keys and "info"
            # are the values
            stationDict = dict(zip(titles, info))
            
            # Add the newly created dictionary inside a list
            stationExtraInfoList.append(stationDict) 

        # Return a list containing all the stations, stored as dictionaries
        return(stationExtraInfoList)

    # Merge basic info gathered from the Open Data (json) with the extra info
    # scraped from the website
    def getStationsFullInfo(self, stationsBasicInfo, stationsExtraInfo):
        stationsBasicInfoSorted = sorted(stationsBasicInfo, 
        key=itemgetter("station_id"))
        
        stationsExtraInfoSorted = sorted(stationsExtraInfo, 
        key=itemgetter("id"))
        
        stationsFullInfo = [a | b for (a, b) in zip(stationsExtraInfoSorted, 
        stationsBasicInfoSorted)]
        return(stationsFullInfo)

    # Search and yield stations by typing their names or their unique IDs, it's
    # meant to be used with STATION_INFO.
    def findStation(self, stations, userInput):

        # Remove accents, all the spaces and special chars from the input
        userInputEdit = re.sub('[^A-Za-z0-9]+', '', 
        unidecode.unidecode(userInput))

        for station in stations:
            # Temporarily treat the station names the same as the userInput
            stationEdit = re.sub('[^A-Za-z0-9]+', '', 
            unidecode.unidecode(station['name']))

            if re.search(userInputEdit, stationEdit, re.IGNORECASE) or re.search(userInput, 
            station['station_id'], re.IGNORECASE):
                yield station

    # Sort all the stations by chosen key
    def sort(self, stations, key):
        return sorted(stations, key=itemgetter(key))