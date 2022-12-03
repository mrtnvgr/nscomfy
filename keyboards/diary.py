from keyboards.keyboard import Keyboard

import logging


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

    def parse(self, text):
        if text not in ["Всё", "Расписание", "Задания", "Оценки"]:
            return

        dateanswer, message_id = self.master.askUserAboutDate(self.user_id)
        if not dateanswer:
            return True

        diary_kwargs = {}

        if text == "Расписание":
            diary_kwargs["show_tasks"] = False
            diary_kwargs["show_marks"] = False
        elif text == "Задания":
            diary_kwargs["only_tasks"] = True
        elif text == "Оценки":
            diary_kwargs["only_marks"] = True

        logging.info(f'{self.user_id}: "{text}" diary request')

        self.master.editButtons(self.user_id, message_id, "Подождите...", [])

        diary = self.master.ns.getDiary(self.user_id, dateanswer, **diary_kwargs)
        if not diary:
            self.master.tg_api.deleteMessage(self.user_id, message_id)
            return True

        self.master.tg_api.deleteMessage(self.user_id, message_id)

        for day in diary:
            text, buttons = day

            self.master.sendButtons(self.user_id, text, buttons, parse_mode="HTML")

        return True
