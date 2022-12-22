import logging
from urllib.parse import unquote_plus

from callbacks.callback import Callback


class DeleteAccount(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)
        current_account = unquote_plus(button_data[0])

        logging.info(f"[NS] {self.user_id}: delete account")

        user = self.master.master.config["users"][self.user_id]
        user["accounts"].pop(current_account)

        self.master.ns.logout(self.user_id)
        user["current_account"] = None

        self.master.master.saveConfig()

        self.master.tg_api.deleteMessage(self.user_id, message_id)
