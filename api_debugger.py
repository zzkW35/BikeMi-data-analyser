from num2words import num2words
# TODO: Convert numerical input into words in
# a proper manner, excluding the station number
import bikemi
import re
import unidecode

STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"
STATUS_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_status.json"

api = bikemi.BikeMiApi()

# Search and *PRINT* stations by typing their names or their unique IDs, it's
# meant to be used with STATION_INFO.
def findStationPrinter(stations):
    userInput = input("What station are you searching for? ")

    # Remove accents, all the spaces and special chars from the input
    userInputEdit = re.sub('[^A-Za-z0-9]+', '', 
    unidecode.unidecode(userInput))

    for station in stations:
        # Temporarily treat the station names the same as the userInput
        stationEdit = re.sub('[^A-Za-z0-9]+', '', 
        unidecode.unidecode(station['name']))

        if re.search(userInputEdit, stationEdit, re.IGNORECASE) or re.search(userInput, 
        station['station_id'], re.IGNORECASE):
            print("")
            print("Name:", station['name'])
            print("ID:", station['station_id'])
            print("Address:", station['address'])
            print("Capacity:", station['capacity'])
            print("Bikes:", station['bike'])
            print("Electric Bikes:", station['ebike'])
            print("Electric Bikes with childseat:", 
            station['ebike_with_childseat'])
            print("Available docks:", station['availableDocks'])
            print("")                
            askFullData = input("Do you want to have full data displayed? ")
            if askFullData.lower() == "yes" or askFullData.lower() == "y":
                print(station)

# This class is meant to be used with STATUS_INFO
def stationStatus(stations):
    userInput = input("What station are you investigating? -Enter its ID- ")
    for station in stations:
        if re.search(userInput, station['station_id'], re.IGNORECASE):
            print(station)


stationsBasicInfo = api.jsonDecoder(STATION_INFO)
stationsExtraInfo = api.getStationsExtraInfo()
stationsFullInfo = api.getStationsFullInfo(stationsBasicInfo, stationsExtraInfo)

findStationPrinter(stationsFullInfo)