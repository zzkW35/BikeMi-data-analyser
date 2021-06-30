from emojis import encode

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


class Tools:
    def build_menu(self, buttons, n_cols, header_buttons=None, footer_buttons=None):
        """Function to build the Inline Keyboard Button menu"""
        menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu

    def callback_query(self, update, context):
        """Display the Inline Keyboard Buttons when the user taps on the "Main Menu" button"""
        query = update.callback_query
        reply_markup = self.custom_keyboard()
        # CallbackQueries need to be answered, even if no notification to the user is needed
        query.answer()
        if query.data == "main_menu_callback":
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=encode(":arrow_down: Choose a function from the menu below"),
                reply_markup=reply_markup,
            )

    def custom_keyboard(self):
        """Function to setup the Keyboard Button menu"""
        search_keyboard = KeyboardButton(text=encode(":mag_right: Search Station"))
        nearest_keyboard = KeyboardButton(text=encode(":walking: Nearest Station"))
        location_keyboard = KeyboardButton(
            text=encode(":round_pushpin: Send current location"),
            request_location=True,
        )

        custom_keyboard = [[search_keyboard] + [nearest_keyboard], [location_keyboard]]
        return ReplyKeyboardMarkup(
            custom_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            selective=True,
        )

    def inline_keyboard_buttons(self, station_raw):
        """Display Inline Keyboard Buttons for the Map coordinates and to go back to Main Menu"""
        button_list = []
        # Add the GMaps location button to the button list
        location_link = (
            "https://www.google.com/maps/search/?api=1&query="
            + str(station_raw["lat"])
            + ","
            + str(station_raw["lon"])
        )
        text = encode(":round_pushpin: Open in Maps")
        button_list.append(InlineKeyboardButton(text=text, url=location_link))
        # Add the main menu button to the button list
        reply_markup = self.custom_keyboard()
        button_list.append(
            InlineKeyboardButton(
                text=encode(":gear: Main Menu"),
                callback_data="main_menu_callback",
            )
        )
        reply_markup = InlineKeyboardMarkup(
            self.build_menu(button_list, n_cols=1)
        )  # n_cols = 1 is for single column and mutliple rows
        return reply_markup
