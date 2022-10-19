from typing import Dict
import requests


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
            return response

    def getUpdates(self, offset):

        payload = {"timeout": 60000, "offset": offset}
        return self.method("getUpdates", payload)

    def sendMessage(self, user_id, text):
        return self.method("sendMessage", {"text": text}, user_id)

    @staticmethod
    def getUserIdFromUpdate(update):
        return update["message"]["chat"]["id"]


class TelegramHandler:
    def __init__(self, master):
        self.master = master

        token = self.master.config["telegram"]["token"]
        self.tg_api = TelegramAPI(token)

    def getUpdates(self):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset)

        if updates != []:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        for update in updates:

            self.updateHandler(update)

    def updateHandler(self, update):
        text = update["message"]["text"]

        user_id = self.tg_api.getUserIdFromUpdate(update)

        if text == "/start":

            self.tg_api.sendMessage(user_id, "test")
