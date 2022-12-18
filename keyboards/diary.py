from keyboards.keyboard import Keyboard


class Diary(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Задания", "Расписание", "Оценки"])
        self.keyboard.append(["Всё"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):
        if text not in ["Всё", "Расписание", "Задания", "Оценки"]:
            return

        callback_data = f"/getDiary {text}"

        buttons = [
            [
                {"text": "Вчера", "callback_data": f"{callback_data} yd"},
                {"text": "Сегодня", "callback_data": f"{callback_data} td"},
                {"text": "Завтра", "callback_data": f"{callback_data} tm"},
            ],
            [
                {"text": "Прошлая", "callback_data": f"{callback_data} lw"},
                {"text": "Текущая", "callback_data": f"{callback_data} cw"},
                {"text": "Следующая", "callback_data": f"{callback_data} nw"},
            ],
        ]

        self.master.sendButtons(self.user_id, "Выберите дату:", buttons)

        return True
