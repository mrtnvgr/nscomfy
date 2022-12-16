import logging

import util
from keyboards.keyboard import Keyboard


class MainMenu(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        if not self.master.ns.checkSession(self.user_id):
            self.ok = False
            return
        api = self.master.ns.sessions[self.user_id]

        student_info = f"Ученик: {api.student_info['name']}"

        firstRow = ["Дневник", "Оценки"]

        self.master.ns.setOverdueCount(self.user_id)
        if api._overdue_count > 0:
            overdueCount = f"\nТочки: {api._overdue_count}"
            firstRow.append("Точки")
        else:
            overdueCount = ""

        if api._unreaded_mail_messages > 0:
            unreaded = api._unreaded_mail_messages
            unreaded = f"\nНепрочитанные письма: {unreaded}"
        else:
            unreaded = ""

        studentText = f"{student_info}{overdueCount}{unreaded}"

        self.text = f"<b>Главное меню</b>\n\n{studentText}\n\n"

        self.keyboard.append(firstRow)
        self.keyboard.append(["Информация"])
        self.keyboard.append(["Настройки", "Выйти"])

        self.one_time_keyboard = False

    def parse(self, text):

        if text == "Выйти":

            self.master.forceLogout(self.user_id)

        elif text == "Точки":

            days = self.master.ns.getOverdueTasks(self.user_id)
            if days:
                for day in days:
                    self.master.tg_api.sendMessage(self.user_id, day)
            else:
                self.master.tg_api.sendMessage(self.user_id, "Нету! :3")
            return True

        elif text == "Дневник":

            self.master.sendKeyboard(self.user_id, "diary")
            return True

        elif text == "Оценки":

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

            convertmark = lambda mark: util.mark_to_sign(mark)

            for subjectName, marks in subject_marks.items():

                if settings["general"]["shorten_subjects"]:
                    subjectName = util.shortenSubjectName(subjectName)

                line = f"\n{subjectName}: "

                rational_marks = [i for i in marks if i is not None]
                average = round(sum(rational_marks) / len(rational_marks), 1)
                if settings["term_marks"]["round_marks"]:
                    line += f"<b>{round(average + 0.001)}</b> ({average})\n"
                else:
                    line += f"<b>{average}</b>\n"

                line += " ".join(map(convertmark, marks))

                text.append(line)

            self.master.editButtons(
                self.user_id, message_id, "\n".join(text), [], parse_mode="HTML"
            )

            return True

        elif text == "Настройки":

            self.master.sendKeyboard(self.user_id, "settings")
            return True

        elif text == "Информация":

            self.master.sendKeyboard(self.user_id, "info")
            return True
