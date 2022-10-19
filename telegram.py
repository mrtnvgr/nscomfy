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

    def getUpdates(self, offset, limit):

        payload = {"timeout": 60000, "offset": offset}
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

    def getUpdates(self, limit=100):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset, limit)

        if updates != []:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        return updates

    def parseUpdates(self, updates):

        for update in updates:

            self.updateHandler(update)

    def updateHandler(self, update):
        text = update["message"]["text"]

        user_id = self.tg_api.getUserIdFromUpdate(update)
        
        # First time
        if user_id not in self.master.config["users"]:

            self.askForAccount(user_id)
        
        # Check if user is currently logged in
        if self.master.config["users"][user_id]["current_session"]:
            print("Logged in! Here starts main menu code")

        # Login menu
        else:
            pass
    
    def askForAccount(self, user_id):

        session = {}

        session["url"] = self.askUser(user_id, "Напишите url:")
        session["login"] = self.askUser(user_id, "Напишите login:")
        session["password"] = self.askUser(user_id, "Напишите password:")
        name = self.askUser(user_id, "Напишите имя сессии:")
        
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

    def sendKeyboard(self, user_id):
        """Send different keyboards to user"""

        # Default keyboard values
        keyboard = {"keyboard": [], "one_time_keyboard": True, "resize_keyboard": True}

        # # First time
        # if user_id not in self.master.config["users"]:
        #     keyboard["keyboard"].append(["Test"])
        #     self.tg_api.sendKeyboard(user_id, "First time placeholder", keyboard)
