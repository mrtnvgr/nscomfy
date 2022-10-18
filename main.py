#!/usr/bin/env python

from telegram import TelegramHandler
import json


class Main:
    def __init__(self):

        self.config = json.load(open("config.json"))
        self.checkconfig()

        self.telegram = TelegramHandler(self)

        self.loop()
   
    def checkconfig(self):

        if "telegram" not in self.config:
            self.config["telegram"] = {}
        
        if "token" not in self.config["telegram"]:
            raise Exception("Specify telegram token")

    def saveConfig(self):
        json.dump(self.config, open("config.json", "w"), indent=4)

    def loop(self):

        while True:

            self.telegram.getUpdates()


if __name__ == "__main__":
    Main()
