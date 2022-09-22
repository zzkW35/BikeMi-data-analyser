from bikemi_data_analyser.api.bikemi import BikeMiApi
from bikemi_data_analyser.telegram_bot.tools import Tools

import os
import logging
import sys

from emojis import encode
from functools import wraps
from geopy.geocoders import MapBox
from telegram import (
    ChatAction,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from threading import Thread


class TelegramBot:
    STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"

    tools = Tools()
    api = BikeMiApi()

    # Logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # Start command
    def start(self, update, context):
        reply_markup = self.tools.custom_keyboard()

        update.message.reply_text(
            encode(":arrow_down: Choose a function from the menu below"),
            reply_markup=reply_markup,
        )

    # BikeMi time

    def pull_stations(self):
        """Access the API and create vars"""
        get_stations_basic_info = self.api.json_decoder(self.STATION_INFO)
        stations_extra_info = self.api.get_stations_extra_info()
        stations_full_info = self.api.get_stations_full_info(
            get_stations_basic_info, stations_extra_info
        )
        return stations_full_info

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

    def search_station(self, update, context, place):
        # Typing...
        context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        stations_full_info = self.pull_stations()

        for station_raw in self.api.find_station(stations_full_info, place):
            if station_raw != None:
                station = self.print_result(station_raw)
                reply_markup = self.tools.inline_keyboard_buttons(station_raw)
                # Send Text
                update.message.reply_text(
                    station,
                    reply_markup=reply_markup,
                )
            else:
                update.message.reply_text(
                    encode(
                        ":x: This BikeMi station doesn't exist, please choose a new command"
                    ),
                    reply_markup=self.tools.custom_keyboard(),
                )

    def search_nearest(self, update, context, place):
        # Typing...
        context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        # Setup MapBox
        mapbox_token = os.environ.get("MAPBOX_TOKEN")
        geolocator = MapBox(mapbox_token)
        proximity = (45.464228552423435, 9.191557965278111)  # Duomo
        location = geolocator.geocode(place, proximity=proximity)

        stations_full_info = self.pull_stations()
        station_raw = self.api.get_nearest_station(
            stations_full_info, location.latitude, location.longitude
        )
        reply_markup = self.tools.inline_keyboard_buttons(station_raw)

        # Generate Text Message
        station = self.print_result(station_raw)
        nearest_station = "The nearest station is: \n" + station
        # Send text
        update.message.reply_text(
            nearest_station,
            reply_markup=reply_markup,
        )

    def get_location(self, update, context):
        # Typing...
        context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        # Store user's latitute and longitude
        user_location = update.message["location"]
        latitude = float(user_location["latitude"])
        longitude = float(user_location["longitude"])

        stations_full_info = self.pull_stations()
        station_raw = self.api.get_nearest_station(
            stations_full_info, latitude, longitude
        )
        reply_markup = self.tools.inline_keyboard_buttons(station_raw)

        # Generate Text Message
        station = self.print_result(station_raw)
        nearest_station = "The nearest station is: \n" + station
        # Send text
        update.message.reply_text(
            nearest_station,
            reply_markup=reply_markup,
        )

    # Start ConversationHandler functions
    HANDLE_COMMAND = range(1)

    def read_command(self, update: Update, context: CallbackContext) -> int:

        if update.message.text == "/search" or update.message.text == encode(
            ":mag_right: Search Station"
        ):
            update.message.reply_text(
                encode(":mag_right: What station are you searching for? \n \n /cancel")
            )
            context.user_data["command"] = "search"

        elif update.message.text == "/nearest" or update.message.text == encode(
            ":walking: Nearest Station"
        ):
            update.message.reply_text(
                encode(
                    ":walking: Enter a place to get the nearest station \n \n /cancel"
                )
            )
            context.user_data["command"] = "nearest"

        elif update.message.text == "/location":
            reply_markup = self.tools.custom_keyboard()
            update.message.reply_text(
                encode(
                    ":round_pushpin: Share your current location to get the nearest station to you \n \n /cancel"
                ),
                reply_markup=reply_markup,
            )
            context.user_data["command"] = "location"

        elif update.message.text == "/cancel":
            reply_markup = self.tools.custom_keyboard()
            update.message.reply_text(
                encode(":thumbsup: Canceled!"), reply_markup=reply_markup
            )
            context.user_data.clear()
            return ConversationHandler.END

        else:
            update.message.reply_text(
                encode(
                    ":exclamation: I don't recognise such command, please select a new one from below"
                ),
                reply_markup=self.tools.custom_keyboard(),
            )
            context.user_data.clear()
            return ConversationHandler.END

        return self.HANDLE_COMMAND

    def handle_command(self, update: Update, context: CallbackContext) -> int:
        context.user_data["place"] = update.message.text
        place = context.user_data["place"]
        context.user_data["location"] = update.message["location"]

        if context.user_data["command"] == "search":
            self.search_station(update, context, place)

        if context.user_data["command"] == "nearest":
            self.search_nearest(update, context, place)

        if context.user_data["command"] == "location":
            self.get_location(update, context)

        return ConversationHandler.END

    def cancel_command(self, update: Update, context: CallbackContext) -> int:
        """Cancels and ends the conversation."""
        reply_markup = self.tools.custom_keyboard()
        update.message.reply_text(
            encode(":thumbsup: Canceled!"), reply_markup=reply_markup
        )
        context.user_data.clear()
        return ConversationHandler.END

    def wrong_input(self, update: Update, context: CallbackContext) -> int:
        reply_markup = self.tools.custom_keyboard()
        update.message.reply_text(
            "That isn't the name of a BikeMi station, cancelling...",
            reply_markup=reply_markup,
        )
        context.user_data.clear()
        return ConversationHandler.END

    # End ConversationHandler functions

    def main(self):
        telegram_token = os.environ.get("TELEGRAM_TOKEN")
        updater = Updater(token=telegram_token, use_context=True)

        # Register handlers
        self.dispatcher = updater.dispatcher

        # Start command
        start_handler = CommandHandler("start", self.start)
        self.dispatcher.add_handler(start_handler)

        # Function to stop and restart the bot from the chat
        def stop_and_restart():
            """Gracefully stop the Updater and replace the current process with a new one"""
            updater.stop()
            os.execl(sys.executable, sys.executable, *sys.argv)

        # Function to stop the bot from the chat
        def restart(update, context):
            update.message.reply_text("Bot is restarting...")
            Thread(target=stop_and_restart).start()

        # Handler to stop the bot
        self.dispatcher.add_handler(
            CommandHandler("r", restart, filters=Filters.user(username="@zzkW35"))
        )

        # Build conv handler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("search", self.read_command),
                MessageHandler(
                    Filters.regex(encode(":mag_right: Search Station")),
                    self.read_command,
                ),
                CommandHandler("nearest", self.read_command),
                MessageHandler(
                    Filters.regex(encode(":walking: Nearest Station")),
                    self.read_command,
                ),
                CommandHandler("location", self.read_command),
                MessageHandler(
                    Filters.text
                    & ~(
                        Filters.location
                        | Filters.regex("/search")
                        | Filters.regex("/nearest")
                        | Filters.regex("/location")
                        | Filters.regex(encode(":mag_right: Search Station"))
                        | Filters.regex(encode(":walking: Nearest Station"))
                    ),
                    self.read_command,
                ),
            ],
            states={
                self.HANDLE_COMMAND: [
                    MessageHandler(
                        (Filters.text | Filters.location)
                        & ~(
                            Filters.command
                            | Filters.regex(encode(":mag_right: Search Station"))
                            | Filters.regex(encode(":walking: Nearest Station"))
                        ),
                        self.handle_command,
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel_command),
                CommandHandler("search", self.wrong_input),
                MessageHandler(
                    Filters.regex(encode(":mag_right: Search Station")),
                    self.wrong_input,
                ),
                CommandHandler("nearest", self.wrong_input),
                MessageHandler(
                    Filters.regex(encode(":walking: Nearest Station")),
                    self.wrong_input,
                ),
                CommandHandler("location", self.wrong_input),
            ],
        )

        self.dispatcher.add_handler(conv_handler)

        # Get Location handler
        get_location_handler = MessageHandler(Filters.location, self.get_location)
        self.dispatcher.add_handler(get_location_handler)

        # Callback query handler
        main_menu_handler = CallbackQueryHandler(self.tools.callback_query)
        self.dispatcher.add_handler(main_menu_handler)

        # Start Bot
        updater.start_polling()
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


bot = TelegramBot()

if __name__ == "__main__":
    bot.main()
