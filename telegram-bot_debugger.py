import bikemi
import emoji
import os
import logging
import sys

from functools import wraps
from geopy.geocoders import MapBox
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultDocument,
    ChatAction,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Location,
)
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from threading import Thread
from typing import Union, List

STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)

# Start command
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter a BikeMi station name to gather info",
    )


# BikeMi time

# Access the API and create vars
def pull_stations():
    api = bikemi.BikeMiApi()
    get_stations_basic_info = api.json_decoder(STATION_INFO)
    stations_extra_info = api.get_stations_extraInfo()
    stations_full_info = api.get_stations_full_info(
        get_stations_basic_info, stations_extra_info
    )
    return stations_full_info


# Function to build the button menu
def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


"""
def city(update,context):
  list_of_cities = ['Erode','Coimbatore','London', 'Thunder Bay', 'California']
  button_list = []
  for each in list_of_cities:
     button_list.append(InlineKeyboardButton(each, callback_data = each))
  reply_markup=InlineKeyboardMarkup(build_menu(button_list,n_cols=1)) #n_cols = 1 is for single column and mutliple rows
  context.bot.send_message(chat_id=update.message.chat_id, text='Choose from the following',reply_markup=reply_markup)
"""


def print_result(station_raw):
    stationInfo = (
        "Name: "
        + str(station_raw["name"])
        + "\nID: "
        + str(station_raw["station_id"])
        + "\nAddress: "
        + str(station_raw["address"])
        + "\nBikes: "
        + str(station_raw["bike"])
        + "\nElectric Bikes: "
        + str(station_raw["ebike"])
        + "\nElectric Bikes with childseat: "
        + str(station_raw["ebike_with_childseat"])
        + "\nAvailable docks: "
        + str(station_raw["availableDocks"])
    )

    return stationInfo


def maps_button(station_raw):
    button_list = []
    location_link = (
        "https://www.google.com/maps/search/?api=1&query="
        + str(station_raw["lat"])
        + ","
        + str(station_raw["lon"])
    )

    text = emoji.emojize(":pushpin: Open in Maps")

    # Add the GMaps location button to the button list
    button_list.append(InlineKeyboardButton(text=text, url=location_link))
    reply_markup = InlineKeyboardMarkup(
        build_menu(button_list, n_cols=1)
    )  # n_cols = 1 is for single column and mutliple rows
    return reply_markup


def search_station(update, context):
    # Typing...
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    api = bikemi.BikeMiApi()
    stations_full_info = pull_stations()

    for station_raw in api.find_station(stations_full_info, " ".join(context.args)):
        station = print_result(station_raw)
        reply_markup = maps_button(station_raw)
        # Send Text
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=station, reply_markup=reply_markup
        )


def find_nearest(update, context):
    # Typing...
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    api = bikemi.BikeMiApi()
    stations_full_info = pull_stations()
    textInput = " ".join(context.args)
    mapbox_token = os.environ.get("MAPBOX_TOKEN")

    geolocator = MapBox(mapbox_token)
    location = geolocator.geocode(textInput)
    station_raw = api.get_nearest_station(
        stations_full_info, location.latitude, location.longitude
    )
    reply_markup = maps_button(station_raw)

    # Text Message
    station = print_result(station_raw)
    nearest_station = "The nearest station is: \n" + station

    # Send text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=nearest_station,
        reply_markup=reply_markup,
    )


def ask_location(update, context):
    location_keyboard = KeyboardButton(
        text="Send Current Location", request_location=True
    )
    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Would you mind sharing your location with me?",
        reply_markup=reply_markup,
    )


def get_location(update, context):
    # Typing...
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    # Store user's latitute and longitude
    user_location = update.message["location"]
    latitude = float(user_location["latitude"])
    longitude = float(user_location["longitude"])

    api = bikemi.BikeMiApi()
    stations_full_info = pull_stations()
    station_raw = api.get_nearest_station(stations_full_info, latitude, longitude)
    reply_markup = maps_button(station_raw)

    # Text Message
    station = print_result(station_raw)
    nearest_station = "The nearest station is: \n" + station

    # Send text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=nearest_station,
        reply_markup=reply_markup,
    )


"""
def ask_search(update, context):

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What station are you searching for?",

        search_station(update, context)
    )
"""


def main():
    telegram_token = os.environ.get("TELEGRAM_DEBUGGING_TOKEN")

    updater = Updater(token=telegram_token, use_context=True)

    # Register handlers
    dispatcher = updater.dispatcher
    dp = updater.dispatcher

    # Start command
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    # Search Station handler
    search_station_handler = CommandHandler("search", search_station)
    dispatcher.add_handler(search_station_handler)

    # Closest Station handler
    find_nearest_handler = CommandHandler("nearest", find_nearest)
    dispatcher.add_handler(find_nearest_handler)

    # Ask Location
    ask_location_handler = CommandHandler("location", ask_location)
    dispatcher.add_handler(ask_location_handler)

    # Get Location
    get_location_handler = MessageHandler(Filters.location, get_location)
    dispatcher.add_handler(get_location_handler)

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        update.message.reply_text("Bot is restarting...")
        Thread(target=stop_and_restart).start()

    dp.add_handler(
        CommandHandler("r", restart, filters=Filters.user(username="@zzkW35"))
    )

    # Start Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
