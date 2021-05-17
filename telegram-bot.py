import bikemi
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from typing import Union, List


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Start command
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter a BikeMi station name to gather info",
    )


# BikeMi time
def search_station(update, context):

    STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"
    api = bikemi.BikeMiApi()
    get_stations_basic_info = api.json_decoder(STATION_INFO)
    stations_extra_info = api.get_stations_extraInfo()
    stations_full_info = api.get_stations_full_info(
        get_stations_basic_info, stations_extra_info
    )

    for stationRaw in api.find_station(stations_full_info, update.message.text):

        station = (
            "Name: "
            + str(stationRaw["name"])
            + "\nID: "
            + str(stationRaw["station_id"])
            + "\nAddress: "
            + str(stationRaw["address"])
            + "\nBikes: "
            + str(stationRaw["bike"])
            + "\nElectric Bikes: "
            + str(stationRaw["ebike"])
            + "\nElectric Bikes with childseat: "
            + str(stationRaw["ebike_with_childseat"])
            + "\nAvailable docks: "
            + str(stationRaw["availableDocks"])
        )

        context.bot.send_message(chat_id=update.effective_chat.id, text=station)


def main():
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token=telegram_token, use_context=True)

    # Register handlers
    dispatcher = updater.dispatcher

    # Start command
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    # Bikemi handler
    search_station_handler = MessageHandler(
        Filters.text & (~Filters.command), search_station
    )
    dispatcher.add_handler(search_station_handler)

    # Start Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
