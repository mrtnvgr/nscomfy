import json
import logging
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
        )

        status_code = response.status_code
        response = response.json()

        if "chat_id" in payload:
            logging.debug(f"[TG] {payload['chat_id']}: {method} {status_code}")

        if response["ok"]:
            return response["result"]
        else:

            # Get rid of annoying bad gateway errors
            if response["error_code"] not in [502, 429]:
                raise Exception(f'{response["error_code"]}: {response["description"]}')
            return {}

    def getUpdates(self, offset, limit, timeout):

        allowed_types = json.dumps(["message", "callback_query"])

        payload = {
            "timeout": timeout,
            "offset": offset,
            "limit": limit,
            "allowed_updates": allowed_types,
        }
        return self.method("getUpdates", payload)

    def sendMessage(self, user_id, text, params={}):
        return self.method("sendMessage", {"text": text} | params, user_id)

    def deleteMessage(self, user_id, msg_id):
        return self.method("deleteMessage", {"chat_id": user_id, "message_id": msg_id})

    def sendKeyboard(self, user_id, text, keyboard):

        if type(keyboard) is dict:

            keyboard = json.dumps(keyboard)

        return self.method(
            "sendMessage", {"text": text, "reply_markup": keyboard}, user_id
        )

    def sendButtons(self, user_id, text, markup, **kwargs):

        if type(markup) is list:
            markup = {"inline_keyboard": markup}
        markup = json.dumps(markup)

        payload = {"text": text, "reply_markup": markup, **kwargs}

        return self.method(
            "sendMessage",
            payload,
            user_id,
        )

    def editButtons(self, user_id, message_id, text, markup, **kwargs):

        if type(markup) is list:
            markup = {"inline_keyboard": markup}
        markup = json.dumps(markup)

        payload = {
            "chat_id": user_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": markup,
            **kwargs,
        }

        return self.method("editMessageText", payload)

    def editPhoto(self, user_id, photo, caption, **kwargs):

        payload = {
            "chat_id": user_id,
            "caption": caption,
            **kwargs,
        }
        files = {}

        if type(photo) is bytes:
            files["photo"] = photo
        else:
            raise Exception(f"invalid photo type: {type(photo)}")

        return self.method("sendPhoto", payload, files=files)

    def sendFile(self, user_id, filename, filebytes: bytes):

        payload = {
            "chat_id": user_id,
        }

        files = {
            "document": (filename, filebytes),
        }

        return self.method("sendDocument", payload, files=files)

    def editMessageReplyMarkup(self, user_id, message_id, markup):

        if type(markup) is list:
            markup = {"inline_keyboard": markup}
        markup = json.dumps(markup)

        payload = {
            "chat_id": user_id,
            "message_id": message_id,
            "reply_markup": markup,
        }

        return self.method("editMessageReplyMarkup", payload)

    @staticmethod
    def getUserIdFromUpdate(update):
        if "message" in update:
            return update["message"]["chat"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["message"]["chat"]["id"]
