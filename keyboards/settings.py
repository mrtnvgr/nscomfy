from keyboards.keyboard import Keyboard

    
class Settings(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Настройки:"

        self.keyboard.append(["Аккаунт"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False
