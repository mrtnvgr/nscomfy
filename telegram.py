from typing import Dict
import requests
import json

from nsapi import NetSchoolAPI


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
            raise Exception(response["description"])

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

    def sendButtons(self, user_id, text, buttons):

        if type(buttons) is dict:
            buttons = json.dumps(buttons)

        return self.method(
            "sendMessage", {"text": text, "reply_markup": buttons}, user_id
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

        self.menuAnswerHandler(user_id, update)

        # Check if user is currently logged in
        if self.master.config["users"][user_id]["current_account"]:
            self.sendMainMenu(user_id)

        # Login menu
        if not self.master.config["users"][user_id]["current_account"]:

            account_name = self.sendKeyboard(user_id, "account_selection")

            if account_name != None:

                if account_name == "+":
                    self.askForAccount(user_id)
                    self.sendMainMenu(user_id)

                elif account_name == "-":

                    name = self.sendKeyboard(user_id, "account_deletion")
                    if name != None:
                        self.master.config["users"][user_id]["accounts"].pop(name)

                else:

                    self.master.config["users"][user_id][
                        "current_account"
                    ] = account_name
                    self.master.saveConfig()

                    self.sendMainMenu(user_id)

    def sendMainMenu(self, user_id):
        self.sendKeyboard(user_id, "mm", get_answer=False)

    def menuAnswerHandler(self, user_id, update):

        if "message" in update:
            text = update["message"]["text"]

            if text == "Выйти":
                self.master.config["users"][user_id]["current_account"] = None
                self.master.saveConfig()

    def askForAccount(self, user_id):

        account = {}

        account["url"] = self.askUser(user_id, "Напишите url:")
        account["login"] = self.askUser(user_id, "Напишите login:")
        account["password"] = self.askUser(user_id, "Напишите password:")

        api = NetSchoolAPI(account["url"])
        districts_response = api.getMunicipalityDistrictList()
        schools_response = api.getSchoolList()

        districts = []
        for district in districts_response:
            districts.append(
                {"text": district["name"], "callback_data": district["id"]}
            )

        self.sendButtons(user_id, "Выберите округ", districts)

        municipalityDistrictId = self.getButtonAnswer()

        addresses = []
        for school in schools_response:
            if school["addressString"] not in addresses:
                if str(school["municipalityDistrictId"]) == municipalityDistrictId:
                    addresses.append(school["addressString"])

        self.sendButtons(user_id, "Выберите aдрес", addresses)

        account["address"] = self.getButtonAnswer()

        schools = []
        for school in schools_response:
            if school["addressString"] == account["address"]:
                schools.append(school["name"])

        # TODO: not send, edit prev message
        # TODO: проверить существует ли аккаунт у пользователя перед логином
        self.sendButtons(user_id, "Выберите школу", schools)

        account["school"] = self.getButtonAnswer()

        name = self.askUser(user_id, "Напишите имя сессии:")

        if not all(account.values()):
            return

        self.addNewUser(user_id)

        self.master.config["users"][user_id]["accounts"][name] = account
        self.master.saveConfig()

    def addNewUser(self, user_id):
        if user_id not in self.master.config["users"]:
            self.master.config["users"][user_id] = {}
            self.master.config["users"][user_id]["accounts"] = {}
            self.master.config["users"][user_id]["current_account"] = None

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
                keyboard["keyboard"].append(["+", "-"])

        elif ktype == "mm":
            text = "Главное меню"

            keyboard["keyboard"].append(["Выйти"])
            keyboard["one_time_keyboard"] = False

        self.tg_api.sendKeyboard(user_id, text, keyboard)

        if get_answer:

            # Get answer
            return self.getUpdate()

    def sendButtons(self, user_id, text, values):

        buttons = []
        for ind, value in enumerate(values):
            if type(value) is str:
                buttons.append([{"text": value, "callback_data": f"/button {ind}"}])
            elif type(value) is dict:
                buttons.append([value])
            elif type(value) is list:
                buttons.append(value)

        markup = {"inline_keyboard": [*buttons]}
        self.tg_api.sendButtons(user_id, text, markup)


class NetSchoolSessionHandler:
    def __init__(self, master):
        self.master = master
        self.sessions = {}

    def checkSession(self, user_id, url):
        if user_id not in self.sessions:
            self.sessions[user_id] = NetSchoolAPI(url)

    def login(self, user_id, url, username, password, school):
        self.checkSession(user_id, url)

        self.sessions[user_id].login(username, password, school)
