import logging

import util
from keyboards.keyboard import Keyboard


class Diary(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Задания", "Расписание", "Оценки"])
        self.keyboard.append(["Всё"])
        self.keyboard.append(["Контрольные работы", "Средний балл"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):

        if text == "Средний балл":
            return self.parseAllMarks(text)
        elif text in ["Всё", "Расписание", "Задания", "Оценки"]:
            callback_data = f"/getDiary {text}"
        elif text == "Контрольные работы":
            callback_data = "/getDiaryTests"
        else:
            return

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

        self.master.tg_api.sendButtons(self.user_id, "Выберите дату:", buttons)

        return True

    def parseAllMarks(self, text):
        logging.info(f"[NS] {self.user_id}: all marks request")

        resp = self.master.tg_api.sendMessage(self.user_id, "Подождите...")
        message_id = resp["message_id"]

        start, end = self.master.ns.getTermDates(self.user_id)

        api = self.master.ns.sessions[self.user_id]

        diary = api.getDiary(start=start, end=end)

        subject_marks = {}

        for day in diary["weekDays"]:

            for lesson in day["lessons"]:

                if "assignments" not in lesson:
                    continue

                marks = []

                for assignment in lesson["assignments"]:

                    if "mark" in assignment:

                        mark = assignment["mark"]["mark"]

                        marks.append(mark)

                subjectName = lesson["subjectName"]

                subject_marks.setdefault(subjectName, [])

                subject_marks[subjectName].extend(marks)

        user = self.master.master.config["users"][self.user_id]
        settings = user["settings"]

        text = ["<b>Оценки за четверть</b>"]

        for subjectName, marks in subject_marks.items():

            if settings["general"]["shorten_subjects"]:
                subjectName = util.shortenSubjectName(subjectName)

            line = f"\n{subjectName}: "

            if settings["term_marks"]["overdue_as_F"]:
                rational_marks = [i if i is not None else 2 for i in marks]
            else:
                rational_marks = [i for i in marks if i is not None]

            average = round(sum(rational_marks) / len(rational_marks), 1)
            rounded = round(average + 0.001)
            if settings["term_marks"]["round_avg_score"]:
                line += f"<b>{rounded}</b> ({average})"
            else:
                line += f"<b>{average}</b>"

            if settings["term_marks"]["show_marks"]:
                line += f'\n{" ".join(map(util.mark_to_sign, marks))}'

            text.append(line)

        self.master.tg_api.editButtons(
            self.user_id, message_id, "\n".join(text), [], parse_mode="HTML"
        )

        return True
