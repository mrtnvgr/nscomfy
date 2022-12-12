from keyboards.keyboard import Keyboard

import util


class Settings(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Настройки:"

        self.keyboard.append(["Аккаунт", "Дневник"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):
        if text == "Аккаунт":

            self.master.sendKeyboard(self.user_id, "settings_account")

            return True

        elif text == "Дневник":

            user = self.master.master.config["users"][self.user_id]
            user_settings = user["settings"]["diary"]

            settings = {
                "Сокращать названия уроков": user_settings["short_subjects"],
            }

            buttons = []

            for setting, value in settings.items():
                status = util.getSwitchEmoji(value)
                buttons.append(
                    {"text": f"[{status}] {setting}", "callback_data": "/changeSetting"}
                )

            self.master.sendButtons(self.user_id, "Настройки дневника:", buttons)

            return True
