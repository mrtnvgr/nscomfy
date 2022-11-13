from nsapi import NetSchoolAPI
from errors import InvalidUrlError, SchoolNotFoundError, LoginError
from ns import NetSchoolSessionHandler
from tgapi import TelegramAPI


class TelegramHandler:
    def __init__(self, master):
        self.master = master
        self.ns = NetSchoolSessionHandler(self)

        token = self.master.config["telegram"]["token"]
        self.tg_api = TelegramAPI(token)

    def getUpdates(self, limit=100, timeout=60):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset, limit, timeout)

        if updates != []:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        return updates

    def getUpdate(self):
        update = self.getUpdates(limit=1)

        if update != None:
            if "message" in update[0]:
                return update[0]["message"]["text"]

    def getButtonAnswer(self):
        update = self.getUpdates(limit=1)

        if update != None:

            if "callback_query" in update[0]:

                query = update[0]["callback_query"]

                buttons = query["message"]["reply_markup"]["inline_keyboard"]

                data = query["data"]

                for button_row in buttons:

                    for button in button_row:

                        if button["callback_data"] == data:

                            if button["callback_data"].startswith("/button"):

                                return button["text"]
                            else:

                                return button["callback_data"]

    def updateHandler(self, update):
        user_id = str(self.tg_api.getUserIdFromUpdate(update))

        # First time
        if user_id not in self.master.config["users"]:
            self.askForAccount(user_id)

        if user_id in self.master.config["users"]:

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
            text = update["message"]["text"]

            current_keyboard = self.master.config["users"][user_id]["current_keyboard"]

            if current_keyboard == "mm":  # Main menu

                if text == "Выйти":

                    self.ns.logout(user_id)
                    self.master.config["users"][user_id]["current_account"] = None
                    self.master.saveConfig()

                elif text == "Точки":

                    text = self.ns.getOverdueTasks(user_id)
                    self.tg_api.sendMessage(user_id, text)
                    return True

                elif text == "Дневник":

                    self.sendKeyboard(user_id, "diary")
                    return True

            elif current_keyboard == "account_selection":

                if text == "Добавить аккаунт":

                    self.askForAccount(user_id)

                elif text == "Удалить аккаунт":

                    if self.master.config["users"][user_id]["accounts"] != {}:
                        self.sendKeyboard(user_id, "account_deletion")
                        return True

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
                                account["school"],
                            )
                        except SchoolNotFoundError:
                            self.tg_api.sendMessage(
                                user_id, "Такой школы не существует"
                            )
                            return
                        except LoginError:
                            self.tg_api.sendMessage(
                                user_id, "Неправильный логин или пароль"
                            )
                            return

                        self.ns.setStudent(user_id, account["student"])

                        self.master.config["users"][user_id]["current_account"] = text
                        self.master.saveConfig()

                        self.tg_api.deleteMessage(user_id, message_id)

                    else:
                        self.tg_api.sendMessage(user_id, "Такого аккаунта нет")

            elif current_keyboard == "account_deletion":

                if text != "Назад":

                    if text in self.master.config["users"][user_id]["accounts"]:
                        self.master.config["users"][user_id]["accounts"].pop(text)
                        self.master.saveConfig()

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

                    diary = self.ns.getDiary(user_id, dateanswer, **diary_kwargs)

                    if not diary:
                        return True
                    text, buttons = diary

                    self.editButtons(
                        user_id, message_id, text, buttons, parse_mode="HTML"
                    )

                    return True

    def askForAccount(self, user_id):

        account = {}

        account["url"] = self.askUser(user_id, "Напишите ссылку на нет город:")

        try:
            api = NetSchoolAPI(account["url"])
        except InvalidUrlError:
            self.tg_api.sendMessage(user_id, "Неправильная ссылка")
            return

        account["login"] = self.askUser(user_id, "Напишите логин:")
        account["password"] = self.askUser(user_id, "Напишите пароль:")

        message_id = self.tg_api.sendMessage(user_id, "Подождите...")["message_id"]

        districts_response = api.getMunicipalityDistrictList()

        districts = []
        for district in districts_response:
            districts.append(
                {"text": district["name"], "callback_data": district["id"]}
            )

        municipalityDistrictId = self.askUserWithButtons(
            user_id, message_id, "Выберите округ", districts
        )
        if not municipalityDistrictId:
            return

        schools_response = api.getSchoolList()

        addresses = []
        for school in schools_response:
            if school["addressString"] not in addresses:
                if str(school["municipalityDistrictId"]) == municipalityDistrictId:
                    addresses.append(school["addressString"])

        account["address"] = self.askUserWithButtons(
            user_id, message_id, "Выберите адрес", addresses
        )
        if not account["address"]:
            return

        schools = []
        for school in schools_response:
            if school["addressString"] == account["address"]:
                schools.append(school["name"])

        account["school"] = self.askUserWithButtons(
            user_id, message_id, "Выберите школу", schools
        )
        if not account["school"]:
            return

        try:
            api.login(account["login"], account["password"], account["school"])
        except SchoolNotFoundError:
            self.tg_api.sendMessage(user_id, "Такой школы не существует")
            return
        except LoginError:
            self.tg_api.sendMessage(user_id, "Неправильный логин или пароль")
            return

        students = api._students
        student_buttons = [student["name"] for student in students]

        account["student"] = self.askUserWithButtons(
            user_id, message_id, "Выберите ученика", student_buttons
        )
        if not account["student"]:
            return

        api.logout()

        self.editButtons(user_id, message_id, "Напишите имя аккаунта:", [])
        name = self.getUpdate()
        if not name:
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

        return self.getUpdate()

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

        if ktype == "account_selection" or ktype == "account_deletion":
            text = "Выберите аккаунт"

            for name in self.master.config["users"][user_id]["accounts"]:
                keyboard["keyboard"].append([name])

            if ktype == "account_selection":
                misc = ["Добавить аккаунт"]

                if self.master.config["users"][user_id]["accounts"] != {}:
                    misc.append("Удалить аккаунт")
                keyboard["keyboard"].append(misc)

            if ktype == "account_deletion":
                keyboard["keyboard"].append(["Назад"])

        elif ktype == "mm":

            self.ns.checkSession(user_id)
            student_info = f"Ученик: {self.ns.sessions[user_id].student_info['name']}"
            activeSessions = f"Пользователей в сети: {len(self.ns.sessions[user_id]._active_sessions)}"
            text = f"Главное меню\n\n{student_info}\n{activeSessions}"

            keyboard["keyboard"].append(["Дневник", "Точки"])
            keyboard["keyboard"].append(["Выйти"])

            keyboard["one_time_keyboard"] = False

        elif ktype == "diary":

            text = "Выберите тип информации:"

            keyboard["keyboard"].append(["Всё"])
            keyboard["keyboard"].append(["Расписание"])
            keyboard["keyboard"].append(["Задания", "Оценки"])
            keyboard["keyboard"].append(["Назад"])

            keyboard["one_time_keyboard"] = False

        self.tg_api.sendKeyboard(user_id, text, keyboard)

        self.master.config["users"][user_id]["current_keyboard"] = ktype
        self.master.saveConfig()

    def sendButtons(self, user_id, text, values):

        markup = self._parseButtons(values)

        return self.tg_api.sendButtons(user_id, text, markup)

    def editButtons(self, user_id, message_id, text, values, parse_mode=""):

        markup = self._parseButtons(values)

        return self.tg_api.editButtons(user_id, message_id, text, markup, parse_mode)

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
