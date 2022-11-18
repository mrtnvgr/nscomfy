from datetime import date as datetime
from datetime import timedelta

import util
from nsapi import NetSchoolAPI


class NetSchoolSessionHandler:
    def __init__(self, master):
        self.master = master
        self.sessions = {}

    def checkSession(self, user_id):

        if user_id not in self.sessions:

            msg_id = self.master.tg_api.sendMessage(user_id, "Подождите...")[
                "message_id"
            ]

            user = self.master.master.config["users"][user_id]

            account_name = user["current_account"]
            if not account_name:
                self.master.tg_api.deleteMessage(user_id, msg_id)
                return False

            account = user["accounts"][account_name]
            url = account["url"]
            username = account["login"]
            password = account["password"]
            school = account["school"]
            student = account["student"]

            self.login(user_id, url, username, password, student, school)

            self.master.tg_api.deleteMessage(user_id, msg_id)

        return True

    def login(self, user_id, url, username, password, student, school):
        self.sessions[user_id] = NetSchoolAPI(url)
        self.sessions[user_id].login(username, password, school)
        self.setStudent(user_id, student)
        self.setOverdueCount(user_id)

    def getOverdueTasks(self, user_id):

        self.checkSession(user_id)

        output = []
        response = self.sessions[user_id].getOverdueTasks()

        dates = {}

        for task in response:
            date = util.formatDate(task["dueDate"])
            if date not in dates:
                dates[date] = []
            dates[date].append(task)

        for date in dates:

            output.append(f"<b>{date}</b>")

            overdues = dates[date]

            for overdue in overdues:

                subject = overdue["subjectName"]
                assignment = overdue["assignmentName"]

                assignment = util.normalizeHTMLText(assignment)

                output.append(f"{subject} ({overdue['type']}):")
                output.append(f"<pre>{assignment}</pre>")

        if output == []:

            return "Нету! :3"

        return "\n".join(output)

    def setOverdueCount(self, user_id):

        self.checkSession(user_id)

        overdues = self.sessions[user_id].getOverdueTasks()
        self.sessions[user_id]._overdue_count = len(overdues)

    def setStudent(self, user_id, student_name):
        return self.sessions[user_id].setStudent(student_name)

    def getDiary(
        self,
        user_id,
        date,
        show_tasks=True,
        show_marks=True,
        only_tasks=False,
        only_marks=False,
    ):

        self.checkSession(user_id)

        today = datetime.today()
        monday = today - timedelta(days=today.weekday())

        if date == "Сегодня":
            start = today
            end = start
        elif date == "Завтра":
            start = today + timedelta(days=1)
            end = start
        elif date == "Вчера":
            start = today - timedelta(days=1)
            end = start
        elif date == "Текущая":
            start = monday
            end = start + timedelta(days=5)
        elif date == "Следующая":
            start = monday + timedelta(days=7)
            end = start + timedelta(days=5)
        elif date == "Прошлая":
            start = monday - timedelta(days=7)
            end = start + timedelta(days=5)
        else:
            return False

        api = self.sessions[user_id]

        diary = api.getDiary(start, end)

        text = []
        buttons = []

        assignIds = self.getAssignIds(diary["weekDays"])
        attachments = api.getDiaryAttachments(assignIds)

        for day in diary["weekDays"]:

            daydate = util.formatDate(day["date"])

            day_text = []

            for lesson in day["lessons"]:

                marks = []
                tasks = []
                attachments_text = []

                showAttachments = False

                if "assignments" in lesson:

                    assignments = lesson["assignments"]
                    for assignment in assignments:

                        if show_marks and "mark" in assignment:

                            mark = assignment["mark"]
                            mark_sign = util.mark_to_sign(mark["mark"])
                            mark_typeid = assignment["typeId"]
                            mark_type = api._assignment_types[mark_typeid]

                            if only_marks:
                                marks.append(f"{mark_sign} | {mark_type}")
                            else:
                                marks.append(mark_sign)
                                showAttachments = True

                        if (
                            show_tasks
                            and "assignmentName" in assignment
                            and not only_marks
                        ):

                            # Получим id типа домашнего задания
                            typeid = api.getAssignmentTypeId("Домашнее задание")

                            assignmentName = assignment["assignmentName"]
                            isEmpty = util.detectEmptyTask(assignmentName)

                            if not isEmpty and assignment["typeId"] == typeid:
                                tasks.append(assignmentName)
                                showAttachments = True

                        if showAttachments:

                            if assignment["id"] in attachments:
                                assignId = assignment["id"]
                                assignment_attachments = attachments[assignId]

                                for attachment in assignment_attachments:
                                    attachmentName = attachment["originalFileName"]
                                    attachmentName = util.normalizeHTMLText(
                                        attachmentName
                                    )

                                    clip = util.getEmoji("PAPERCLIP")

                                    attachmentText = f"{clip} {attachmentName}"

                                    attachmentButton = self.createAttachmentButton(
                                        user_id, attachmentText, attachment
                                    )

                                    attachments_text.append(
                                        f"<b>{attachmentText}</b>\n"
                                    )
                                    buttons.append(attachmentButton)

                name = lesson["subjectName"]
                number = lesson["number"]
                start = lesson["startTime"]
                end = lesson["endTime"]

                name = util.shortenSubjectName(name)

                if only_marks and not marks:
                    continue

                if only_tasks and not tasks:
                    continue

                line = f"\n{number}: {name} ({start} - {end})"
                line = util.normalizeHTMLText(line)
                if marks and not only_tasks:
                    if only_marks:
                        marks_text = "\n".join(marks)
                        line += f"\n{marks_text}"
                    else:
                        line += f" <b>[{', '.join(marks)}]</b>"
                day_text.append(f"{line}\n")

                if tasks:

                    for task in tasks:
                        task = util.normalizeHTMLText(task)
                        day_text.append(f"<pre>{task}</pre>\n")

                if attachments_text:

                    day_text.extend(attachments_text)

            if day_text:
                text.append("\n")
                text.append("\n")
                text.append(f"<b>{daydate}:</b>")
                text += day_text

        if text == []:
            text.append("На эти числа информации нет!")

        return "".join(text), buttons

    def getAssignIds(self, days):

        assignIds = []
        for day in days:
            for lesson in day["lessons"]:
                if "assignments" in lesson:
                    for assignment in lesson["assignments"]:
                        assignIds.append(assignment["id"])

        return assignIds

    def createAttachmentButton(self, user_id, text, attachment):

        aId = attachment["id"]

        api = self.sessions[user_id]
        studentId = api.student_info["id"]

        data = f"/downloadAttachment {studentId} {aId}"
        return {"text": text, "callback_data": data}

    def logout(self, user_id):

        if user_id in self.sessions:
            self.sessions[user_id].logout()
            self.sessions.pop(user_id)
