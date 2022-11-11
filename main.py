#!/usr/bin/env python

from telegram import TelegramHandler
import json
import os


class Main:
    def __init__(self):

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

            updates = self.telegram.getUpdates(timeout=60000)
            self.telegram.parseUpdates(updates)


if __name__ == "__main__":
    Main()
