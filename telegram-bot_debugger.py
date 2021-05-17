import bikemi
import emojis
import os
import logging
import sys

from functools import wraps
from geopy.geocoders import MapBox
from telegram import (
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultDocument,
    KeyboardButton,
    Location,
    ReplyKeyboardMarkup,
)
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from threading import Thread
from typing import Union, List

STATION_INFO = "https://gbfs.urbansharing.com/bikemi.com/station_information.json"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)

# Function to build the Inline Keyboard Button menu
def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# Function to setup the Keyboard Button menu
def custom_keyboard():
    search_keyboard = KeyboardButton(text=emojis.encode(":mag_right: Search Station"))
    nearest_keyboard = KeyboardButton(text="Nearest Station")
    location_keyboard = KeyboardButton(
        text=emojis.encode(":round_pushpin: Send current location"),
        request_location=True,
    )

    custom_keyboard = [[search_keyboard] + [nearest_keyboard], [location_keyboard]]
    return ReplyKeyboardMarkup(
        custom_keyboard, resize_keyboard=True, one_time_keyboard=True, selective=True
    )


# Start command
def start(update, context):
    reply_markup = custom_keyboard()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Choose a function from the menu below",
        reply_markup=reply_markup,
    )


# BikeMi time

# Access the API and create vars
def pull_stations():
    api = bikemi.BikeMiApi()
    get_stations_basic_info = api.json_decoder(STATION_INFO)
    stations_extra_info = api.get_stations_extra_info()
    stations_full_info = api.get_stations_full_info(
        get_stations_basic_info, stations_extra_info
    )
    return stations_full_info


# Print station's info
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


# Display Inline Keyboard Button for the Map coordinates
def maps_button(station_raw):
    button_list = []
    location_link = (
        "https://www.google.com/maps/search/?api=1&query="
        + str(station_raw["lat"])
        + ","
        + str(station_raw["lon"])
    )
    text = emojis.encode(":round_pushpin: Open in Maps")

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

    for station_raw in api.find_station(stations_full_info, update.message.text):
        station = print_result(station_raw)
        reply_markup = maps_button(station_raw)
        # Send Text
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=station, reply_markup=reply_markup
        )


def search_nearest(update, context):
    # Typing...
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    mapbox_token = os.environ.get("MAPBOX_TOKEN")
    text_input = update.message.text
    geolocator = MapBox(mapbox_token)
    proximity = (45.464228552423435, 9.191557965278111)  # Duomo
    location = geolocator.geocode(text_input, proximity=proximity)
    api = bikemi.BikeMiApi()
    stations_full_info = pull_stations()
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

    # Generate Text Message
    station = print_result(station_raw)
    nearest_station = "The nearest station is: \n" + station
    # Send text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=nearest_station,
        reply_markup=reply_markup,
    )


def main():
    telegram_token = os.environ.get("TELEGRAM_DEBUGGING_TOKEN")

    updater = Updater(token=telegram_token, use_context=True)
    search_list = [
        "search",
        "Search",
        "/search",
        emojis.encode(":mag_right: Search Station"),
    ]
    nearest_list = ["nearest", "Nearest", "/nearest", "Nearest Station"]
    location_list = [
        "location",
        "Location",
        "/location",
        emojis.encode(":round_pushpin: Send current location"),
    ]
    easteregg_list = ["Deez", "deez"]
    command_list = search_list + nearest_list + location_list + easteregg_list

    # Register handlers
    dispatcher = updater.dispatcher

    # Start command
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    def browser(update, context):
        # Search Station
        for element in search_list:
            if update.message.text == element:
                update.message.reply_text(text="What station are you searching for?")
                # Search station handler
                search_station_handler = MessageHandler(
                    Filters.text & (~Filters.command), search_station
                )
                dispatcher.add_handler(search_station_handler)

        # Nearest station
        for element in nearest_list:
            if update.message.text == element:
                update.message.reply_text(
                    text="Enter a place to get the nearest station"
                )
                # Nearest Station handler
                search_nearest_handler = MessageHandler(
                    Filters.text & (~Filters.command), search_nearest
                )
                dispatcher.add_handler(search_nearest_handler)

        # Location
        for element in location_list:
            if update.message.text == element:
                update.message.reply_text(
                    text="Share your current location to get the nearest station to you"
                )
                # Get Location handler
                get_location_handler = MessageHandler(Filters.location, get_location)
                dispatcher.add_handler(get_location_handler)
        
        # Easter Egg
        for element in easteregg_list:
            if update.message.text == element:
                update.message.reply_text(text="NUUUUUUUUUUUUUUUUUUUUUUUUTZ")

    # Bowser handler
    for element in command_list:
        browser_handler = MessageHandler(Filters.regex(element), browser)
        dispatcher.add_handler(browser_handler)

    # Get Location handler
    get_location_handler = MessageHandler(Filters.location, get_location)
    dispatcher.add_handler(get_location_handler)

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
    dispatcher.add_handler(
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
