import util
from keyboards.keyboard import Keyboard


class Settings(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):

        self.settings_types = {
            "Общее": "Общие настройки:",
            "Дневник": "Настройки дневника:",
            "Средний балл": "Настройки оценок за четверть:",
            "Отладка": "Настройки для отладки:",
        }

        self.text = "Настройки:"

        self.keyboard.append(list(self.settings_types.keys()))
        self.keyboard.append(["Аккаунт", "Назад"])

        self.one_time_keyboard = False

    def parse(self, text):
        if text == "Аккаунт":

            self.master.sendKeyboard(self.user_id, "settings_account")

            return True

        elif text in self.settings_types.keys():

            settings = util.SETTINGS_SCHEMA

            buttons = []

            user = self.master.master.config["users"][self.user_id]  # noqa: F841

            for setting, setting_data in settings.items():
                if setting_data["group"] != text:
                    continue
                state = eval(setting_data["path"])
                status = util.getSwitchEmoji(state)
                setting_name = setting_data["name"]
                buttons.append(
                    [
                        {
                            "text": f"{status} {setting_name}",
                            "callback_data": f"/showSetting {setting}",
                        }
                    ]
                )

            settings_type = self.settings_types.get(text, text)

            self.master.tg_api.sendButtons(self.user_id, settings_type, buttons)

            return True
