from keyboards.keyboard import Keyboard


class Settings(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Настройки:"

        self.keyboard.append(["Аккаунт"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):
        if text == "Аккаунт":

            self.master.sendKeyboard(self.user_id, "settings_account")

            return True
