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

            settings = (
                ("Сокращать названия уроков", "shorten_subjects"),
            )

            buttons = []

            for setting_name, setting in settings:
                state = user_settings[setting]
                status = util.getSwitchEmoji(state)
                buttons.append(
                    {"text": f"{status} {setting_name}", "callback_data": f"/showSetting diary.{setting}"}
                )

            self.master.sendButtons(self.user_id, "Настройки дневника:", buttons)

            return True
