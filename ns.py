from datetime import date as datetime
from datetime import timedelta
from itertools import zip_longest
import logging

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

            try:
                self.login(user_id, url, username, password, student, school)
            except Exception as exception:
                self.handleLoginError(user_id, msg_id, exception)
                return

            self.master.tg_api.deleteMessage(user_id, msg_id)

        return True

    def login(self, user_id, url, username, password, student, school):
        logging.info(f"[NS] {user_id}: log in")
        self.sessions[user_id] = NetSchoolAPI(user_id, url)
        self.sessions[user_id].login(username, password, school)
        self.setStudent(user_id, student)

    def getOverdueTasks(self, user_id):

        logging.info(f"[NS] {user_id}: overdue tasks request")

        if not self.checkSession(user_id):
            return

        response = self.sessions[user_id].getOverdueTasks()

        dates = {}

        for task in response:
            date = util.humanizeDate(task["dueDate"])
            if date not in dates:
                dates[date] = []
            dates[date].append(task)

        days = []
        for date in dates:

            day = []

            day.append(f"<b>{date}</b>\n")

            overdues = dates[date]

            for overdue in overdues:

                subject = overdue["subjectName"]
                assignment = overdue["assignmentName"]

                assignment = util.normalizeHTMLText(assignment)

                day.append(f"{subject} ({overdue['type']}):")
                day.append(f"<pre>{assignment}</pre>\n")

            days.append("\n".join(day))

        return days

    def setOverdueCount(self, user_id):

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

        if not self.checkSession(user_id):
            return

        today = datetime.today()
        monday = today - timedelta(days=today.weekday())

        if date == "td":
            start = today
            end = start
        elif date == "tm":
            start = today + util.getTomorrowDelta(today)
            end = start
        elif date == "yd":
            start = today - util.getYesterdayDelta(today)
            end = start
        elif date == "cw":
            start = monday
            end = start + timedelta(days=5)
        elif date == "nw":
            start = monday + timedelta(days=7)
            end = start + timedelta(days=5)
        elif date == "lw":
            start = monday - timedelta(days=7)
            end = start + timedelta(days=5)
        else:
            return False

        api = self.sessions[user_id]

        diary = api.getDiary(start, end)
        if not diary:
            return

        assignIds = self.getAssignIds(diary["weekDays"])
        attachments = api.getDiaryAttachments(assignIds)

        days = []

        for day in diary["weekDays"]:

            day_output = self.parseDiaryDay(
                user_id,
                api,
                day,
                attachments,
                show_tasks,
                show_marks,
                only_tasks,
                only_marks,
            )
            if day_output[0]:
                days.append(day_output)

        if not days:
            days.append(["На эти числа информации не найдено.", []])

        return days

    def parseDiaryDay(
        self,
        user_id,
        api,
        day,
        attachments,
        show_tasks,
        show_marks,
        only_tasks,
        only_marks,
    ):

        daydate = util.humanizeDate(day["date"])

        text = []
        buttons = []

        for lesson in day["lessons"]:

            marks = []
            markComments = []
            tasks = []
            attachments_text = []

            showAttachments = False

            if "assignments" in lesson:

                assignments = lesson["assignments"]
                for assignment in assignments:

                    if show_marks and not only_tasks:

                        if "mark" in assignment:

                            mark = assignment["mark"]
                            mark_sign = util.mark_to_sign(mark["mark"])
                            mark_typeid = assignment["typeId"]
                            mark_type = api._assignment_types[mark_typeid]

                            if only_marks:
                                marks.append(f"{mark_sign} | {mark_type}")
                            else:
                                marks.append(mark_sign)
                                showAttachments = True

                        if "markComment" in assignment:

                            comment = assignment["markComment"]["name"]

                            markComments.append(comment)

                    if show_tasks and "assignmentName" in assignment:

                        assignmentName = assignment["assignmentName"]
                        isEmpty = util.detectEmptyTask(assignmentName)

                        if not isEmpty:

                            if not only_marks:

                                # Получим id типа домашнего задания
                                typeid = api.getAssignmentTypeId("Домашнее задание")

                                if assignment["typeId"] == typeid:
                                    tasks.append(assignmentName)
                                    showAttachments = True

                            else:

                                if "mark" in assignment:

                                    tasks.append(assignmentName)

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
                                        user_id,
                                        assignment["id"],
                                        attachmentText,
                                        attachment,
                                    )

                                    attachments_text.append(
                                        f"<b>{attachmentText}</b>\n"
                                    )
                                    buttons.append(attachmentButton)

            name = lesson["subjectName"]
            number = lesson["number"]
            start = lesson["startTime"]
            end = lesson["endTime"]

            user = self.master.master.config["users"][user_id]
            diary_settings = user["settings"]["diary"]

            if diary_settings["shorten_subjects"]:
                name = util.shortenSubjectName(name)

            if only_marks and not marks:
                continue

            if only_tasks and not tasks:
                continue

            line = ""

            if diary_settings["show_subject_number"]:
                line += f"{number}: "

            line += name

            if diary_settings["show_subject_time"]:
                line += f"({start} - {end})"

            line = "\n" + line

            line = util.normalizeHTMLText(line)
            if marks and not only_marks:
                line += f" <b>[{', '.join(marks)}]</b>"
            text.append(f"{line}\n")

            cloud = util.getEmoji("SPEECH BALLOON")

            for mark, comm, task, attach in zip_longest(
                marks, markComments, tasks, attachments_text
            ):

                if mark and only_marks:
                    text.append(f"{mark}\n")

                if comm:
                    comm = util.normalizeHTMLText(comm)
                    text.append(f"{cloud}: {comm}\n")

                if task:
                    task = util.normalizeHTMLText(task)
                    text.append(f"<pre>{task}</pre>\n")

                if attach:
                    text.extend(attach)

        if text:
            text.insert(0, f"<b>{daydate}</b>\n")

        return "".join(text), buttons

    def getSchoolInfo(self, user_id, full: bool):

        if not self.checkSession(user_id):
            return
        api = self.sessions[user_id]

        school_info = api.getSchoolInfo()
        if not school_info:
            return

        commonInfo = school_info["commonInfo"]
        managementInfo = school_info["managementInfo"]
        contactInfo = school_info["contactInfo"]
        otherInfo = school_info["otherInfo"]

        params = [
            ["Главное:", "--SPACER--", False],
            ["Название", commonInfo["schoolName"], True],
            ["Полное название", commonInfo["fullSchoolName"], False],
            ["Контакты:", "--SPACER--", False],
            ["Адрес", contactInfo["juridicalAddress"], True],
            ["Номер телефона", contactInfo["phones"], True],
            ["Факс", contactInfo["fax"], False],
            ["Почта", contactInfo["email"], True],
            ["Сайт", contactInfo["web"], True],
            ["Руководство:", "--SPACER--", False],
            ["Директор", managementInfo["director"], True],
            ["Зам директора по УВР", managementInfo["principalUVR"], False],
            ["Зам директора по АХЧ", managementInfo["principalAHC"], False],
            ["Зам директора по ИТ", managementInfo["principalIT"], False],
            ["Юридические данные:", "--SPACER--", False],
            ["ИНН", otherInfo["inn"], True],
            ["КПП", otherInfo["kpp"], False],
            ["ОГРН/ОГРНИП", otherInfo["ogrn"], False],
            ["Код ОКПО", otherInfo["okpo"], False],
            ["Код ОКАТО", otherInfo["okato"], False],
            ["Код ОКОГУ", otherInfo["okogu"], False],
            ["ОКОПФ", otherInfo["okopf"], False],
            ["ОКФС", otherInfo["okfs"], False],
            ["ОКВЕД", otherInfo["okved"], False],
        ]

        text = []

        for param_key, param_value, param_full in params:

            if param_full or full:

                if param_value:

                    if param_value == "--SPACER--":
                        text.append(f"\n\n<b>{param_key}</b>")
                    else:
                        param_value = util.normalizeHTMLText(param_value)
                        text.append(f"\n{param_key}: <pre>{param_value}</pre>")

        return "\n".join(text)

    def getAccountInfo(self, user_id):

        if not self.checkSession(user_id):
            return
        api = self.sessions[user_id]

        account_info = api.getAccountInfo()
        if not account_info:
            return

        birthDate = account_info["birthDate"]
        if birthDate:
            birthDate = util.formatDate(birthDate)

        firstName = account_info["firstName"]
        lastName = account_info["lastName"]
        middleName = account_info["middleName"]
        name = f"{firstName} {lastName} {middleName}"

        roles = account_info["roles"]
        roles = list(map(util.getRole, roles))
        roles = ["Роль", roles]
        if len(roles[1]) > 1:
            roles[0] = "Роли"
        roles[1] = ", ".join(roles[1])

        params = [
            ["ФИО", name],
            roles,
            ["Логин", account_info["loginName"]],
            ["Дата рождения", birthDate],
            ["Телефон", account_info["mobilePhone"]],
            ["Почта", account_info["email"]],
        ]

        text = []

        for param_name, param_value in params:
            if param_value:
                param_value = util.normalizeHTMLText(param_value)
                text.append(f"\n{param_name}: <pre>{param_value}</pre>")

        return "\n".join(text)

    def getBirthdays(self, user_id, monthId):

        if not self.checkSession(user_id):
            return
        api = self.sessions[user_id]

        monthId = monthId.split("_")[1]
        monthName = util.getMonthName(monthId)

        birthdays = api.getBirthdays(monthId)

        bd_sorted = {}

        # Restructure birthdays info
        for birthday in birthdays:

            bd_date = util.formatDate(birthday["birthdate"])

            if bd_date not in bd_sorted:
                bd_sorted[bd_date] = []

            bd_sorted[bd_date].append(
                {
                    "fio": birthday["fio"],
                    "role": util.getRole(birthday["role"]),
                }
            )

        # Convert data to text

        text = []

        text.append(f"<b>{monthName}</b>")

        for bd_date, bd_list in bd_sorted.items():

            for bd_data in bd_list:
                text.append(f"\n<b>{bd_date}:</b>")
                fio = bd_data["fio"]
                role = bd_data["role"]
                text.append(f"{fio}")
                text.append(f"Роль: {role}")

        if len(text) < 2:
            text.append(f"На {monthName} нет именинников.")

        return "\n".join(text)

    def getBirthdayMonths(self, user_id):

        if not self.checkSession(user_id):
            return
        api = self.sessions[user_id]

        filters = api.getBirthdayFilters()
        if not filters:
            return

        if "filterSources" not in filters:
            return

        sources = filters["filterSources"]
        for source in sources:
            if source["filterId"] == "MonthsFilter":
                months = source["items"]
                return {month["title"]: month["value"] for month in months}

    def getUserPhoto(self, user_id):

        if not self.checkSession(user_id):
            return
        api = self.sessions[user_id]

        photo = api.getUserPhoto()

        return photo

    def getAssignIds(self, days):

        assignIds = []
        for day in days:
            for lesson in day["lessons"]:
                if "assignments" in lesson:
                    for assignment in lesson["assignments"]:
                        assignIds.append(assignment["id"])

        return assignIds

    def createAttachmentButton(self, user_id, assignId, text, attachment):

        attachId = attachment["id"]

        api = self.sessions[user_id]
        studentId = api.student_info["id"]

        data = f"/downloadAttachment {studentId} {assignId} {attachId}"
        return {"text": text, "callback_data": data}

    def handleLoginError(self, user_id, msg_id, exception):
        error_msg, _ = self.master.master.handleError(user_id, exception)
        self.master.editButtons(user_id, msg_id, error_msg, [])
        self.master.forceLogout(user_id)
        self.master.sendKeyboard(user_id, "account_selection")

    def logout(self, user_id):

        if user_id in self.sessions:
            logging.info(f"[NS] {user_id}: log out")
            self.sessions[user_id].logout()
            self.sessions.pop(user_id)

    def allLogout(self):
        sessions = self.sessions.copy()
        if sessions:
            logging.log(logging.EXIT, "Logging out of all sessions")
            for user_id in sessions:
                self.logout(user_id)
