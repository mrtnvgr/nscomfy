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

            settings = util.SETTINGS_SCHEMA

            buttons = []

            for setting, setting_data in settings.items():
                state = eval(setting_data["path"])
                status = util.getSwitchEmoji(state)
                setting_name = setting_data["name"]
                buttons.append(
                    {
                        "text": f"{status} {setting_name}",
                        "callback_data": f"/showSetting {setting}",
                    }
                )

            self.master.sendButtons(self.user_id, "Настройки дневника:", buttons)

            return True
