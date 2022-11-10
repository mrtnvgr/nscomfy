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

            # Get rid of annoying bad gateway errors
            if response["error_code"] != 502:
                raise Exception(f'{response["error_code"]}: {response["description"]}')
            return {}

    def getUpdates(self, offset, limit, timeout):

        payload = {"timeout": timeout, "offset": offset, "limit": limit}
        return self.method("getUpdates", payload)

    def sendMessage(self, user_id, text):
        return self.method("sendMessage", {"text": text}, user_id)

    def deleteMessage(self, user_id, msg_id):
        return self.method("deleteMessage", {"chat_id": user_id, "message_id": msg_id})

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

    def editButtons(self, user_id, message_id, text, markup, parse_mode):

        if type(markup) is dict:
            markup = json.dumps(markup)

        payload = {
            "chat_id": user_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": markup,
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode

        return self.method("editMessageText", payload)

    @staticmethod
    def getUserIdFromUpdate(update):
        if "message" in update:
            return update["message"]["chat"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["message"]["chat"]["id"]
