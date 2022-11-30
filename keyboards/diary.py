from keyboards.keyboard import Keyboard

class Diary(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Всё"])
        self.keyboard.append(["Расписание"])
        self.keyboard.append(["Задания", "Оценки"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False
