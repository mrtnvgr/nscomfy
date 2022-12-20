#!/usr/bin/env python

import argparse
import json
import logging
import os
import signal

from requests.exceptions import ConnectionError, JSONDecodeError

from errors import *
from telegram import TelegramHandler


class Main:
    def __init__(self):

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self.exitSignal)

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--log-level", choices=["info", "debug", "error"], default="debug"
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
                updates = self.telegram.getUpdates()
                for update in updates:
                    self.telegram.updateHandler(update)
            except ConnectionError:
                pass
            except Exception:
                logging.exception("Exception catched!", exc_info=True)

    def handleError(self, user_id, exception):

        errorMessages = {
            SchoolNotFoundError: "Такой школы не существует.",
            LoginError: "Неправильные данные для входа в аккаунт.",
            UnsupportedRoleError: "Ваш тип аккаунта не поддерживается."
            'Бот предназначен для аккаунтов с ролями "Student"(Ученик) или "Parent"(Родитель)',
            InvalidUrlError: "Введённая ссылка неправильная или не является нетгородом.",
            UnknownStudentError: "Указанного ученика аккаунта больше не существует.",
        }

        ignoreErrors = [
            JSONDecodeError,  # Битые данные с нет города
            TechnicalMaintenanceError,  # тех. работы
        ]

        unknownMessage = "Что-то пошло не так, повторите попытку позже."

        exceptionName = exception.__class__.__name__

        unknownErr = exception.__class__ not in errorMessages
        ignoreErr = exception.__class__ in ignoreErrors

        errorMessage = errorMessages.get(exception.__class__, unknownMessage)

        if not unknownErr or ignoreErr:
            logging.error(f'[NS] {user_id}: "{exceptionName}" exception')
        else:
            logging.exception(f"[NS] {user_id}: unknown exception!")

        return errorMessage, unknownErr

    def exit(self):
        self.telegram.ns.allLogout()

    def exitSignal(self, *args):
        logging.log(logging.EXIT, f"Signal catched: {args}")
        self.exit()
        exit(1)


if __name__ == "__main__":
    Main()
