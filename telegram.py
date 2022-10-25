from typing import Dict
import requests
import json

from nsapi import NetSchoolAPI
from errors import InvalidUrlError, SchoolNotFoundError, LoginError


class TelegramAPI:
    def __init__(self, token):

        self.session = requests.Session()
        self.token = token

    def method(self, method, payload: Dict, user_id=None, **kwargs):

        if user_id:
            payload["chat_id"] = user_id
            payload["parse_mode"] = "HTML"

        response = self.session.get(
            f"https://api.telegram.org/bot{self.token}/{method}",
            params=payload,
            **kwargs,
        ).json()

        if response["ok"]:
            return response["result"]
        else:
            raise Exception(f'{response["error_code"]}: {response["description"]}')

    def getUpdates(self, offset, limit, timeout):

        payload = {"timeout": timeout, "offset": offset, "limit": limit}
        return self.method("getUpdates", payload)

    def sendMessage(self, user_id, text):
        return self.method("sendMessage", {"text": text}, user_id)

    def sendKeyboard(self, user_id, text, keyboard):

        if type(keyboard) is dict:

            keyboard = json.dumps(keyboard)

        return self.method(
            "sendMessage", {"text": text, "reply_markup": keyboard}, user_id
        )

    def sendButtons(self, user_id, text, markup):

        if type(markup) is dict:
            markup = json.dumps(markup)

        return self.method(
            "sendMessage", {"text": text, "reply_markup": markup}, user_id
        )

    def editButtons(self, user_id, message_id, text, markup):

        if type(markup) is dict:
            markup = json.dumps(markup)

        return self.method(
            "editMessageText",
            {
                "chat_id": user_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": markup,
            },
        )

    @staticmethod
    def getUserIdFromUpdate(update):
        if "message" in update:
            return update["message"]["chat"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["message"]["chat"]["id"]


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

    def parseUpdates(self, updates):

        for update in updates:

            self.updateHandler(update)

    def updateHandler(self, update):
        user_id = str(self.tg_api.getUserIdFromUpdate(update))

        # First time
        if user_id not in self.master.config["users"]:

            self.askForAccount(user_id)

        if self.menuAnswerHandler(user_id, update):
            return

        # Check if user is currently logged in
        if self.master.config["users"][user_id]["current_account"]:
            self.sendMainMenu(user_id)

        # Login menu
        if not self.master.config["users"][user_id]["current_account"]:

            self.sendLoginMenu(user_id)

    def sendLoginMenu(self, user_id):
        self.sendKeyboard(user_id, "account_selection", get_answer=False)

    def sendMainMenu(self, user_id):
        self.sendKeyboard(user_id, "mm", get_answer=False)

    def menuAnswerHandler(self, user_id, update):

        if "message" in update:
            text = update["message"]["text"]

            current_keyboard = self.master.config["users"][user_id]["current_keyboard"]

            if current_keyboard == "mm":  # Main menu

                if text == "Выйти":

                    self.ns.logout(user_id)
                    self.master.config["users"][user_id]["current_account"] = None
                    self.master.saveConfig()

            elif current_keyboard == "account_selection":

                if text == "Добавить аккаунт":

                    if self.askForAccount(user_id):
                        self.sendMainMenu(user_id)
                        return True

                elif text == "Удалить аккаунт":

                    if self.master.config["users"][user_id]["accounts"] != {}:
                        self.sendKeyboard(user_id, "account_deletion", get_answer=False)
                        return True

                else:

                    if text in self.master.config["users"][user_id]["accounts"]:
                        self.tg_api.sendMessage(user_id, "Подождите...")
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

                        self.master.config["users"][user_id]["current_account"] = text
                        self.master.saveConfig()

                    else:
                        self.tg_api.sendMessage(user_id, "Такого аккаунта нет")

            elif current_keyboard == "account_deletion":

                if text != "Назад":

                    if text in self.master.config["users"][user_id]["accounts"]:
                        self.master.config["users"][user_id]["accounts"].pop(text)
                        self.master.saveConfig()

    def askForAccount(self, user_id):

        account = {}

        account["url"] = self.askUser(user_id, "Напишите url:")

        try:
            api = NetSchoolAPI(account["url"])
        except InvalidUrlError:
            self.tg_api.sendMessage(user_id, "Неправильный url")
            return

        account["login"] = self.askUser(user_id, "Напишите логин:")
        account["password"] = self.askUser(user_id, "Напишите пароль:")

        message_id = self.tg_api.sendMessage(user_id, "Подождите...")["message_id"]

        districts_response = api.getMunicipalityDistrictList()
        schools_response = api.getSchoolList()

        districts = []
        for district in districts_response:
            districts.append(
                {"text": district["name"], "callback_data": district["id"]}
            )

        self.editButtons(user_id, message_id, "Выберите округ", districts)

        municipalityDistrictId = self.getButtonAnswer()
        if municipalityDistrictId == None:
            return

        addresses = []
        for school in schools_response:
            if school["addressString"] not in addresses:
                if str(school["municipalityDistrictId"]) == municipalityDistrictId:
                    addresses.append(school["addressString"])

        self.editButtons(user_id, message_id, "Выберите aдрес", addresses)

        account["address"] = self.getButtonAnswer()
        if account["address"] == None:
            return

        schools = []
        for school in schools_response:
            if school["addressString"] == account["address"]:
                schools.append(school["name"])

        self.editButtons(user_id, message_id, "Выберите школу", schools)

        account["school"] = self.getButtonAnswer()
        if account["school"] == None:
            return

        name = self.askUser(user_id, "Напишите имя сессии:")
        if name == None:
            return

        if not all(account.values()):
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

    def sendKeyboard(self, user_id, ktype, get_answer=True):
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

            if self.ns.checkSession(user_id, None):
                student_info = (
                    f"Ученик: {self.ns.sessions[user_id].student_info['name']}"
                )
                text = f"Главное меню\n\n{student_info}"

                keyboard["keyboard"].append(["Выйти"])
                keyboard["one_time_keyboard"] = False

        self.tg_api.sendKeyboard(user_id, text, keyboard)

        self.master.config["users"][user_id]["current_keyboard"] = ktype
        self.master.saveConfig()

        if get_answer:

            # Get answer
            return self.getUpdate()

    def sendButtons(self, user_id, text, values):

        markup = self._parseButtons(values)

        return self.tg_api.sendButtons(user_id, text, markup)

    def editButtons(self, user_id, message_id, text, values):

        markup = self._parseButtons(values)

        return self.tg_api.editButtons(user_id, message_id, text, markup)

    @staticmethod
    def _parseButtons(values):
        buttons = []

        for ind, value in enumerate(values):
            if type(value) is str:
                buttons.append([{"text": value, "callback_data": f"/button {ind}"}])
            elif type(value) is dict:
                buttons.append([value])
            elif type(value) is list:
                buttons.append(value)

        return {"inline_keyboard": [*buttons]}


class NetSchoolSessionHandler:
    def __init__(self, master):
        self.master = master
        self.sessions = {}

    def checkSession(self, user_id, url):

        if user_id not in self.sessions:

            if url == None:
                user = self.master.config["users"][user_id]
                account_name = user["current_account"]
                account = user["accounts"][account_name]
                url = account["url"]

            self.sessions[user_id] = NetSchoolAPI(url)
            return False
        else:
            return True

    def login(self, user_id, url, username, password, school):
        self.checkSession(user_id, url)

        self.sessions[user_id].login(username, password, school)

    def logout(self, user_id):

        if user_id in self.sessions:
            self.sessions[user_id].logout()
