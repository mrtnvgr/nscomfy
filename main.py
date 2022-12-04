#!/usr/bin/env python

from telegram import TelegramHandler
from errors import *

import json
import os
import signal
import logging
import argparse


class Main:
    def __init__(self):

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self.exitSignal)

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--log-level", choices=["info", "debug", "error"], default="info"
        )
        self.args = parser.parse_args()

        logging.basicConfig(
            format="[%(levelname)s] %(message)s", level=self.args.log_level.upper()
        )

        logging.EXIT = 21

        level_names = {
            logging.INFO: "II",
            logging.DEBUG: "DD",
            logging.WARNING: "WW",
            logging.ERROR: "EE",
            logging.EXIT: "EX",
        }
        for level, name in level_names.items():
            logging.addLevelName(level, name)

        # Turn off requests logger
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        if os.path.exists("config.json"):
            self.config = json.load(open("config.json"))
        else:
            self.config = {}

        self.checkconfig()

        self.telegram = TelegramHandler(self)

        self.loop()

    def checkconfig(self):

        if "telegram" not in self.config:
            self.config["telegram"] = {}

        if "token" not in self.config["telegram"]:
            self.config["telegram"]["token"] = ""
            self.saveConfig()
            raise Exception("Specify telegram token")

        if "users" not in self.config:
            self.config["users"] = {}

        self.saveConfig()

    def saveConfig(self):
        json.dump(self.config, open("config.json", "w"), indent=4, ensure_ascii=False)

    def loop(self):

        while True:

            try:
                updates = self.telegram.getUpdates(timeout=999999)
                for update in updates:
                    self.telegram.updateHandler(update)
            except Exception:
                logging.exception("Exception catched!", exc_info=True)

    def handleError(self, user_id, exception):

        errorMessages = {
            SchoolNotFoundError: "Такой школы не существует!",
            LoginError: "Неправильный логин или пароль!",
            UnsupportedRole: "Ваш тип аккаунта не поддерживается!",
            InvalidUrlError: "Неправильная ссылка!",
        }

        unknownMessage = "Что-то пошло не так! Повторите попытку позже."

        logging.error(f"[NS] {user_id}: {exception.__class__} exception")

        unknownErr = exception.__class__ not in errorMessages
        errorMessage = errorMessages.get(exception.__class__, unknownMessage)

        return errorMessage, unknownErr

    def exit(self):
        self.telegram.ns.allLogout()

    def exitSignal(self, *args):
        logging.log(logging.EXIT, f"Signal catched: {args}")
        self.exit()
        exit(1)


if __name__ == "__main__":
    Main()
