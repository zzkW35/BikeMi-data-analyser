# from num2words import num2words
# TODO: Convert numerical input into words in
# a proper manner, excluding the station number
import bikemi
import re
import unidecode

from geopy.geocoders import Nominatim


STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"
STATUS_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_status.json"

api = bikemi.BikeMiApi()

# Search and *PRINT* stations by typing their names or their unique IDs, it's
# meant to be used with STATION_INFO.
def find_stationPrinter(stations):
    user_input = input("What station are you searching for? ")

    # Remove accents, all the spaces and special chars from the input
    user_inputEdit = re.sub("[^A-Za-z0-9]+", "", unidecode.unidecode(user_input))

    for station in stations:
        # Temporarily treat the station names the same as the user_input
        stationEdit = re.sub("[^A-Za-z0-9]+", "", unidecode.unidecode(station["name"]))

        if user_inputEdit != ("") and (
            re.search(user_inputEdit, stationEdit, re.IGNORECASE)
            or re.search(user_input, station["station_id"], re.IGNORECASE)
        ):
            location_link = (
                "https://www.google.com/maps/search/?api=1&query="
                + str(station["lat"])
                + ","
                + str(station["lon"])
            )
            print("")
            print("Name:", station["name"])
            print("ID:", station["station_id"])
            print("Address:", station["address"])
            print("Capacity:", station["capacity"])
            print("Bikes:", station["bike"])
            print("Electric Bikes:", station["ebike"])
            print("Electric Bikes with childseat:", station["ebike_with_childseat"])
            print("Available docks:", station["availableDocks"])
            print(location_link)
            print("")
            askFullData = input("Do you want to have full data displayed? ")
            if askFullData.lower() == "yes" or askFullData.lower() == "y":
                print(station)


# This class is meant to be used with STATUS_INFO
def stationStatus(stations):
    user_input = input("What station are you investigating? -Enter its ID- ")
    for station in stations:
        if re.search(user_input, station["station_id"], re.IGNORECASE):
            print(station)


get_stations_basic_info = api.json_decoder(STATION_INFO)
get_stations_extraInfo = api.get_stations_extraInfo()
stations_full_info = api.get_stations_full_info(
    get_stations_basic_info, get_stations_extraInfo
)

# print(find_stationPrinter(stations_full_info))
