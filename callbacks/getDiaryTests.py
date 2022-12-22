import logging

import util
from callbacks.callback import Callback


class GetDiaryTests(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)

        if not self.master.ns.checkSession(self.user_id):
            self.master.tg_api.editButtons(
                self.user_id,
                message_id,
                "Перед тем как запросить контрольные работы, войдите в аккаунт.",
                [],
            )
            return True

        logging.info(f"[NS] {self.user_id}: test papers request")

        self.master.tg_api.editButtons(self.user_id, message_id, "Подождите...", [])

        api = self.master.ns.sessions[self.user_id]

        date = util.getDate(button_data[0])
        if not date:
            return

        start, end = date

        diary = api.getDiary(start=start, end=end)
        if not diary:
            return

        importants = {}

        for day in diary["weekDays"]:

            for lesson in day["lessons"]:

                if "assignments" in lesson:

                    for assignment in lesson["assignments"]:

                        typeId = assignment["typeId"]
                        typeId = api._assignment_types[typeId]

                        if typeId not in ["Домашнее задание", "Ответ на уроке"]:

                            dueDate = assignment["dueDate"]
                            importants.setdefault(dueDate, [])
                            importants[dueDate].append(
                                {
                                    "name": assignment["assignmentName"],
                                    "subject": lesson["subjectName"],
                                    "type": typeId,
                                }
                            )

        self.master.tg_api.deleteMessage(self.user_id, message_id)

        if importants == {}:
            self.master.tg_api.sendMessage(
                self.user_id, "На эти числа информации не найдено."
            )
            return True

        user = self.master.master.config["users"][self.user_id]
        general_settings = user["settings"]["general"]

        for date, assignments in importants.items():

            text = []

            date = util.humanizeDate(date)
            text.append(f"<b>{date}</b>")

            for assignment in assignments:

                subject = assignment["subject"]
                if general_settings["shorten_subjects"]:
                    subject = util.shortenSubjectName(subject)

                typeName = assignment["type"]
                text.append(f"\n{subject} ({typeName}):")

                name = util.normalizeHTMLText(assignment["name"])
                text.append(name)

            self.master.tg_api.sendMessage(self.user_id, "\n".join(text))

        return True
