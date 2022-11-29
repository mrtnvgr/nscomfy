from nsapi import NetSchoolAPI
from errors import *
from ns import NetSchoolSessionHandler
from tgapi import TelegramAPI
import util


class TelegramHandler:
    def __init__(self, master):
        self.master = master
        self.ns = NetSchoolSessionHandler(self)

        token = self.master.config["telegram"]["token"]
        self.tg_api = TelegramAPI(token)

        # Set offset to latest update
        self.getInstantUpdates()

    def getUpdates(self, limit=100, timeout=30):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset, limit, timeout)

        if len(updates) > 0:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        return updates

    def getInstantUpdates(self):
        return self.getUpdates(timeout=0)

    def getUpdateText(self):
        update = self.getUpdates(limit=1)

        if update:
            if "message" in update[0]:
                return update[0]["message"].get("text", "")

    def getButtonAnswer(self):
        updates = self.getUpdates(limit=1)
        if updates:
            return self.parseButtonUpdate(updates[0])

    def parseButtonUpdate(self, update, getText=False):

        if update:

            if "callback_query" in update:

                query = update["callback_query"]

                buttons = query["message"]["reply_markup"]["inline_keyboard"]

                data = query["data"]

                for button_row in buttons:

                    for button in button_row:

                        if button["callback_data"] == data:

                            if button["callback_data"].startswith("/button") or getText:
                                return button["text"]
                            else:
                                return button["callback_data"]

    def updateHandler(self, update):
        user_id = str(self.tg_api.getUserIdFromUpdate(update))

        self.addNewUser(user_id)

        if self.menuAnswerHandler(user_id, update):
            return

        # Check if user is currently logged in
        if self.master.config["users"][user_id]["current_account"]:
            self.sendKeyboard(user_id, "mm")

        # Login menu
        if not self.master.config["users"][user_id]["current_account"]:
            self.sendKeyboard(user_id, "account_selection")

    def menuAnswerHandler(self, user_id, update):

        if "message" in update:
            text = update["message"].get("text", "")

            current_keyboard = self.master.config["users"][user_id]["current_keyboard"]

            if current_keyboard == "mm":  # Main menu

                if text == "Выйти":

                    self.forceLogout(user_id)

                elif text == "Точки":

                    days = self.ns.getOverdueTasks(user_id)
                    if days:
                        for day in days:
                            self.tg_api.sendMessage(user_id, day)
                    else:
                        self.tg_api.sendMessage(user_id, "Нету! :3")
                    return True

                elif text == "Дневник":

                    self.sendKeyboard(user_id, "diary")
                    return True

                elif text == "Настройки":

                    self.sendKeyboard(user_id, "settings")
                    return True

                elif text == "Информация":

                    self.sendKeyboard(user_id, "info")
                    return True

            elif current_keyboard == "account_selection":

                if text == "Добавить аккаунт":

                    self.askForAccount(user_id)

                else:

                    if text in self.master.config["users"][user_id]["accounts"]:
                        message_id = self.tg_api.sendMessage(user_id, "Подождите...")[
                            "message_id"
                        ]
                        account = self.master.config["users"][user_id]["accounts"][text]
                        try:
                            self.ns.login(
                                user_id,
                                account["url"],
                                account["login"],
                                account["password"],
                                account["student"],
                                account["school"],
                            )
                        except SchoolNotFoundError:
                            self.handleLoginError(
                                user_id,
                                message_id,
                                "Такой школы не существует!",
                                pop=text,
                            )
                            return
                        except LoginError:
                            self.handleLoginError(
                                user_id,
                                message_id,
                                "Неправильный логин или пароль!",
                                pop=text,
                            )
                            return
                        except UnsupportedRole:
                            self.handleLoginError(
                                user_id,
                                message_id,
                                "Ваш тип аккаунта не поддерживается!",
                                pop=text,
                            )
                            return
                        except:
                            self.handleLoginError(
                                user_id,
                                message_id,
                                "Что-то пошло не так! Повторите попытку позже.",
                                pop=text,
                            )
                            return

                        self.master.config["users"][user_id]["current_account"] = text
                        self.master.saveConfig()

                        self.tg_api.deleteMessage(user_id, message_id)

                    else:
                        self.tg_api.sendMessage(
                            user_id,
                            "Такого аккаунта нет! Пожалуйста используйте кнопки!",
                        )

            elif current_keyboard == "diary":

                if text in ["Всё", "Расписание", "Задания", "Оценки"]:

                    dateanswer, message_id = self.askUserAboutDate(user_id)
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

                    self.editButtons(user_id, message_id, "Подождите...", [])

                    diary = self.ns.getDiary(user_id, dateanswer, **diary_kwargs)
                    if not diary:
                        return True

                    self.tg_api.deleteMessage(user_id, message_id)

                    for day in diary:
                        text, buttons = day

                        self.sendButtons(user_id, text, buttons, parse_mode="HTML")

                    return True

            elif current_keyboard == "settings":

                if text == "Аккаунт":

                    self.sendKeyboard(user_id, "settings_account")

                    return True

            elif current_keyboard == "settings_account":

                if text == "Удалить":

                    if (
                        self.askUser(user_id, 'Для продолжения напишите "Согласен":')
                        == "Согласен"
                    ):

                        current_account = self.master.config["users"][user_id][
                            "current_account"
                        ]
                        self.master.config["users"][user_id]["accounts"].pop(
                            current_account
                        )

                        self.ns.logout(user_id)
                        self.master.config["users"][user_id]["current_account"] = None

                        self.master.saveConfig()

                elif text == "Переименовать":

                    newName = self.askUser(user_id, "Напишите новое название аккаунта:")
                    if not newName:
                        return

                    if not util.checkAccountName(newName):
                        self.tg_api.sendMessage(
                            user_id, "Такое имя аккаунта запрещено!"
                        )
                        return True

                    current_account = self.master.config["users"][user_id][
                        "current_account"
                    ]

                    account = self.master.config["users"][user_id]["accounts"].pop(
                        current_account
                    )

                    self.master.config["users"][user_id]["accounts"][newName] = account
                    self.master.config["users"][user_id]["current_account"] = newName
                    self.master.saveConfig()

                    self.tg_api.sendMessage(
                        user_id,
                        f'Аккаунт "{current_account}" переименован в "{newName}"',
                    )

                elif text == "Сменить ученика":

                    if not self.ns.checkSession(user_id):
                        return
                    api = self.ns.sessions[user_id]

                    buttons = [[student["name"]] for student in api._students]

                    resp = self.sendButtons(user_id, "Выберите ученика:", buttons)
                    message_id = resp["message_id"]

                    answer = self.getButtonAnswer()
                    if not answer:
                        return

                    if answer not in [student["name"] for student in api._students]:
                        return

                    self.tg_api.deleteMessage(user_id, message_id)

                    current_account = self.master.config["users"][user_id][
                        "current_account"
                    ]
                    self.master.config["users"][user_id]["accounts"][current_account][
                        "student"
                    ] = answer
                    self.master.saveConfig()

                    self.forceLogout(user_id)

            elif current_keyboard == "info":

                if text == "Школа":

                    school_info = self.ns.getSchoolInfo(user_id, full=False)
                    if school_info:

                        buttons = [
                            {
                                "text": "Полные данные",
                                "callback_data": "/getFullSchoolInfo",
                            }
                        ]

                        self.sendButtons(user_id, school_info, buttons)

                    return True

                elif text == "Аккаунт":

                    account_info = self.ns.getAccountInfo(user_id)

                    user_photo = self.ns.getUserPhoto(user_id)

                    if account_info:
                        self.tg_api.editPhoto(
                            user_id,
                            user_photo,
                            account_info,
                            parse_mode="HTML",
                        )

                    return True

                elif text == "Бот":

                    text = []

                    users = self.master.config["users"]

                    userCount = len(users)

                    accCount = 0
                    for user in users:
                        accounts = users[user]["accounts"]
                        accCount += len(accounts)

                    giturl = "https://github.com/mrtnvgr/nscomfy"
                    text.append(f"Страница проекта: <a href = '{giturl}'>тут</a>")
                    text.append("Автор: @p13d3z\n")

                    text.append(f"Количество пользователей: <b>{userCount}</b>")
                    text.append(f"Количество аккаунтов: <b>{accCount}</b>")

                    self.tg_api.sendMessage(
                        user_id,
                        "\n".join(text),
                        params={"disable_web_page_preview": True},
                    )

                    return True

        elif "callback_query" in update:

            button_data = self.parseButtonUpdate(update)

            if not button_data:
                return

            button_data = button_data.split(" ")

            if button_data[0] == "/downloadAttachment":

                message_id = self.tg_api.sendMessage(user_id, "Подождите...")["message_id"]

                if not self.ns.checkSession(user_id):
                    self.editButtons(
                        user_id, message_id, "Перед тем как скачивать, нужно зайти в аккаунт!", []
                    )
                    return True

                api = self.ns.sessions[user_id]

                studentId = api.student_info["id"]

                if str(studentId) != button_data[1]:
                    self.editButtons(
                        user_id, message_id, "Текущий аккаунт не имеет доступа к этому вложению!", []
                    )
                    return True

                assignmentId = button_data[2]
                # Для получения доступа к вложению нужно запросить список вложений задания
                api.getDiaryAttachments(assignmentId)

                attachmentType = button_data[3]
                attachmentId = button_data[4]

                attachmentUrl = api.getAttachmentUrl(attachmentId)
                attachment = api.request(attachmentUrl).content
                attachmentSize = len(attachment)

                maxSize = 1000000
                if attachmentType in ["jpg", "jpeg", "png"]:
                    maxSize *= 10
                else:
                    maxSize *= 50

                if attachmentSize > maxSize:
                    self.editButtons(user_id, message_id, "Размер файла слишком большой!", [])
                    return True

                attachmentName = self.parseButtonUpdate(update, getText=True)

                self.tg_api.deleteMessage(user_id, message_id)

                self.tg_api.sendFile(user_id, attachmentName, attachment)

                return True

            elif button_data[0] == "/getFullSchoolInfo":

                message_id = update["callback_query"]["message"]["message_id"]

                school_info = self.ns.getSchoolInfo(user_id, full=True)
                if school_info:
                    self.editButtons(
                        user_id, message_id, school_info, [], parse_mode="HTML"
                    )

                return True

    def askForAccount(self, user_id):

        account = {}

        account["url"] = self.askUser(user_id, "Напишите ссылку на нет город:")
        if not account["url"]:
            return

        try:
            api = NetSchoolAPI(account["url"])
        except InvalidUrlError:
            self.tg_api.sendMessage(user_id, "Неправильная ссылка!")
            return

        account["login"] = self.askUser(user_id, "Напишите логин:")
        if not account["login"]:
            return
        account["password"] = self.askUser(user_id, "Напишите пароль:")
        if not account["password"]:
            return

        message_id = self.tg_api.sendMessage(user_id, "Подождите...")["message_id"]

        try:
            districts_response = api.getMunicipalityDistrictList()
            schools_response = api.getSchoolList()
        except:
            self.editButtons(
                user_id, message_id, "Что-то пошло не так! Повторите попытку позже.", []
            )
            return

        districts = []
        for district in districts_response:
            districts.append(
                {"text": district["name"], "callback_data": district["id"]}
            )

        municipalityDistrictId = self.askUserWithButtons(
            user_id, message_id, "Выберите округ:", districts
        )
        if not municipalityDistrictId:
            return

        addresses = []
        for school in schools_response:
            if school["addressString"] not in addresses:
                if str(school["municipalityDistrictId"]) == municipalityDistrictId:
                    addresses.append(school["addressString"])

        account["address"] = self.askUserWithButtons(
            user_id, message_id, "Выберите адрес:", addresses
        )
        if not account["address"]:
            return

        schools = []
        for school in schools_response:
            if school["addressString"] == account["address"]:
                schools.append(school["name"])

        account["school"] = self.askUserWithButtons(
            user_id, message_id, "Выберите школу:", schools
        )
        if not account["school"]:
            return

        self.editButtons(user_id, message_id, "Подождите...", [])

        try:
            api.login(account["login"], account["password"], account["school"])
        except SchoolNotFoundError:
            self.editButtons(user_id, message_id, "Такой школы не существует!", [])
            return
        except LoginError:
            self.editButtons(user_id, message_id, "Неправильный логин или пароль!", [])
            return
        except UnsupportedRole:
            self.editButtons(
                user_id, message_id, "Ваш тип аккаунта не поддерживается!", []
            )
            return

        students = api._students
        student_buttons = [student["name"] for student in students]

        account["student"] = self.askUserWithButtons(
            user_id,
            message_id,
            "Выберите ученика:\n(можно изменить в настройках)",
            student_buttons,
        )
        if not account["student"]:
            return

        api.logout()

        self.editButtons(
            user_id,
            message_id,
            "Напишите имя аккаунта:\n(можно изменить в настройках)",
            [],
        )
        name = self.getUpdateText()
        if not name:
            return

        if not util.checkAccountName(name):
            self.tg_api.sendMessage(user_id, "Такое имя аккаунта запрещено!")
            return

        self.addNewUser(user_id)

        self.master.config["users"][user_id]["accounts"][name] = account
        self.master.saveConfig()

        return True

    def addNewUser(self, user_id):
        if user_id not in self.master.config["users"]:
            self.master.config["users"][user_id] = {}
            self.master.config["users"][user_id]["accounts"] = {}
            self.master.config["users"][user_id]["current_account"] = None
            self.master.config["users"][user_id]["current_keyboard"] = None

    def askUser(self, user_id, msg):
        self.tg_api.sendMessage(user_id, msg)

        return self.getUpdateText()

    def askUserWithButtons(self, user_id, message_id, msg, buttons):

        if type(buttons) is list:
            if len(buttons) == 1:
                return buttons[0]

        self.editButtons(user_id, message_id, msg, buttons)
        return self.getButtonAnswer()

    def askUserAboutDate(self, user_id):
        buttons = [
            ["Вчера", "Сегодня", "Завтра"],
            ["Прошлая", "Текущая", "Следующая"],
        ]
        resp = self.sendButtons(user_id, "Выберите дату:", buttons)
        message_id = resp["message_id"]

        dateanswer = self.getButtonAnswer()

        return dateanswer, message_id

    def sendKeyboard(self, user_id, ktype):
        """Send different keyboards to user"""

        # Default keyboard values
        keyboard = {"keyboard": [], "one_time_keyboard": True, "resize_keyboard": True}
        text = ""

        if ktype == "account_selection":
            text = "Выберите аккаунт:"

            accounts = self.master.config["users"][user_id]["accounts"]
            for name in sorted(accounts):
                keyboard["keyboard"].append([name])

            keyboard["keyboard"].append(["Добавить аккаунт"])

        elif ktype == "mm":

            if not self.ns.checkSession(user_id):
                return
            api = self.ns.sessions[user_id]
            student_info = f"Ученик: {api.student_info['name']}"
            activeSessions = f"Пользователей в сети: {len(api._active_sessions)}"

            firstRow = ["Дневник"]

            self.ns.setOverdueCount(user_id)
            if api._overdue_count > 0:
                overdueCount = f"\nТочки: {api._overdue_count}"
                firstRow.append("Точки")
            else:
                overdueCount = ""

            if api._unreaded_mail_messages > 0:
                unreaded = f"\nНепрочитанные письма: {api._unreaded_mail_messages}"
            else:
                unreaded = ""

            text = f"Главное меню\n\n{student_info}{overdueCount}{unreaded}\n\n{activeSessions}"

            keyboard["keyboard"].append(firstRow)
            keyboard["keyboard"].append(["Информация"])
            keyboard["keyboard"].append(["Настройки", "Выйти"])

            keyboard["one_time_keyboard"] = False

        elif ktype == "diary":

            text = "Выберите тип информации:"

            keyboard["keyboard"].append(["Всё"])
            keyboard["keyboard"].append(["Расписание"])
            keyboard["keyboard"].append(["Задания", "Оценки"])
            keyboard["keyboard"].append(["Назад"])

            keyboard["one_time_keyboard"] = False

        elif ktype == "settings":

            text = "Настройки:"

            keyboard["keyboard"].append(["Аккаунт"])
            keyboard["keyboard"].append(["Назад"])

            keyboard["one_time_keyboard"] = False

        elif ktype == "settings_account":

            if not self.ns.checkSession(user_id):
                return
            api = self.ns.sessions[user_id]

            text = "Настройки аккаунта:"

            keyboard["keyboard"].append(["Переименовать", "Удалить"])

            if len(api._students) > 1:
                keyboard["keyboard"].append(["Сменить ученика"])

            keyboard["keyboard"].append(["Назад"])

            keyboard["one_time_keyboard"] = False

        elif ktype == "info":

            text = "Выберите тип информации:"

            keyboard["keyboard"].append(["Аккаунт", "Школа"])
            keyboard["keyboard"].append(["Бот"])
            keyboard["keyboard"].append(["Назад"])

            keyboard["one_time_keyboard"] = False

        self.tg_api.sendKeyboard(user_id, text, keyboard)

        self.master.config["users"][user_id]["current_keyboard"] = ktype
        self.master.saveConfig()

    def sendButtons(self, user_id, text, values, parse_mode=None):

        markup = self._parseButtons(values)

        return self.tg_api.sendButtons(user_id, text, markup, parse_mode)

    def editButtons(self, user_id, message_id, text, values, parse_mode=""):

        markup = self._parseButtons(values)

        return self.tg_api.editButtons(user_id, message_id, text, markup, parse_mode)

    def handleLoginError(self, user_id, message_id, error_msg, pop: str = ""):
        self.editButtons(user_id, message_id, error_msg, [])
        if pop:
            self.master.config["users"][user_id]["accounts"].pop(pop)
            self.master.saveConfig()

    def forceLogout(self, user_id):
        self.ns.logout(user_id)
        self.master.config["users"][user_id]["current_account"] = None
        self.master.saveConfig()

    @staticmethod
    def _parseButtons(values):
        buttons = []

        ind = 0
        for value in values:
            if type(value) is str:
                buttons.append([{"text": value, "callback_data": f"/button {ind}"}])
            elif type(value) is dict:
                buttons.append([value])
            elif type(value) is list:
                if type(value[0]) is dict:
                    buttons.append(value)
                else:
                    values = []
                    for button in value:
                        ind += 1
                        values.append(
                            {"text": button, "callback_data": f"/button {ind}"}
                        )
                    buttons.append(values)
            ind += 1

        return {"inline_keyboard": [*buttons]}
