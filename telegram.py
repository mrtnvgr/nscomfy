from typing import Dict
import requests
import json


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

    @staticmethod
    def getUserIdFromUpdate(update):
        return update["message"]["chat"]["id"]


class TelegramHandler:
    def __init__(self, master):
        self.master = master

        token = self.master.config["telegram"]["token"]
        self.tg_api = TelegramAPI(token)

    def getUpdates(self, limit=100, timeout=60000):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset, limit, timeout)

        if updates != []:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        return updates

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
        if self.master.config["users"][user_id]["current_session"]:
            self.sendMainMenu(user_id)

        # Login menu
        if not self.master.config["users"][user_id]["current_session"]:

            session_name = self.sendKeyboard(user_id, "session_selection")

            if session_name != None:

                if session_name == "+":
                    self.askForAccount(user_id)
                    self.sendMainMenu(user_id)

                elif session_name == "-":

                    name = self.sendKeyboard(user_id, "session_deletion")
                    if name != None:
                        self.master.config["users"][user_id]["sessions"].pop(name)

                else:

                    self.master.config["users"][user_id][
                        "current_session"
                    ] = session_name
                    self.master.saveConfig()

                    self.sendMainMenu(user_id)

    def sendMainMenu(self, user_id):
        self.sendKeyboard(user_id, "mm", get_answer=False)

    def menuAnswerHandler(self, user_id, update):
        text = update["message"]["text"]

        if text == "Выйти":
            self.master.config["users"][user_id]["current_session"] = None
            self.master.saveConfig()

    def askForAccount(self, user_id):

        session = {}

        session["url"] = self.askUser(user_id, "Напишите url:")
        session["login"] = self.askUser(user_id, "Напишите login:")
        session["password"] = self.askUser(user_id, "Напишите password:")
        name = self.askUser(user_id, "Напишите имя сессии:")

        if not all(session.values()):
            return

        self.addNewUser(user_id)

        self.master.config["users"][user_id]["current_session"] = None

        self.master.config["users"][user_id]["sessions"][name] = session
        self.master.saveConfig()

    def addNewUser(self, user_id):
        if user_id not in self.master.config["users"]:
            self.master.config["users"][user_id] = {}
            self.master.config["users"][user_id]["sessions"] = {}

    def askUser(self, user_id, msg):
        self.tg_api.sendMessage(user_id, msg)

        response = self.getUpdates(limit=1)

        if response != []:
            return response[0]["message"]["text"]

    def sendKeyboard(self, user_id, ktype, get_answer=True):
        """Send different keyboards to user"""

        # Default keyboard values
        keyboard = {"keyboard": [], "one_time_keyboard": True, "resize_keyboard": True}
        text = ""

        if ktype == "session_selection" or ktype == "session_deletion":
            text = "Выберите аккаунт"

            for name in self.master.config["users"][user_id]["sessions"]:
                keyboard["keyboard"].append([name])

            if ktype == "session_selection":
                keyboard["keyboard"].append(["+", "-"])

        elif ktype == "mm":
            text = "Главное меню"

            keyboard["keyboard"].append(["Выйти"])
            keyboard["one_time_keyboard"] = False

        self.tg_api.sendKeyboard(user_id, text, keyboard)

        if get_answer:

            # Get answer
            update = self.getUpdates(limit=1)
            if update != []:
                return update[0]["message"]["text"]
