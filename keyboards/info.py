from keyboards.keyboard import Keyboard


class Info(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Аккаунт", "Школа"])
        self.keyboard.append(["Бот"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False
