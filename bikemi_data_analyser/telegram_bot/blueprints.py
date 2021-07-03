from emojis import encode


class Blueprints:
    def print_command_info(self):
        """Display information about the available commands"""
        welcome_text = (
            encode(
                ":mag_right: Search Station: Type any BikeMi station name to get info"
            )
            + "\n \n"
            + encode(
                ":walking: Nearest Station: Type any place in Milan to get the nearest station to it"
            )
            + "\n \n"
            + encode(
                ":round_pushpin: Send Location: Share your current location to get the nearest station to you"
            )
        )
        return welcome_text

    def print_result(self, station_raw):
        """Display station's info"""
        stationInfo = (
            encode(":busstop: Name: ")
            + station_raw["name"]
            + "\n"
            + encode(":round_pushpin: Address: ")
            + station_raw["address"]
            + "\n"
            + encode(":bike: Bikes: ")
            + station_raw["bike"]
            + "\n"
            + encode(":zap: Electric Bikes: ")
            + station_raw["ebike"]
            + "\n"
            + encode(":seat: Electric Bikes with Child Seat: ")
            + station_raw["ebike_with_childseat"]
            + "\n"
            + encode(":parking: Available docks: ")
            + station_raw["availableDocks"]
        )
        return stationInfo
