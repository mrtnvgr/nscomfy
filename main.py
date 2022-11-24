#!/usr/bin/env python

from telegram import TelegramHandler

import json
import os

import signal


class Main:
    def __init__(self):

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self.exitSignal)

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
                updates = self.telegram.getUpdates(timeout=60000)
                for update in updates:
                    self.telegram.updateHandler(update)
            except Exception as ex:
                self.exit()
                print("EXIT: Raising exception for debug")
                raise ex

    def exit(self):
        print("EXIT: Logging out of all sessions")
        self.telegram.ns.allLogout()

    def exitSignal(self, *args):
        print(f"EXIT: Signal catched: {args}")
        self.exit()
        exit(1)


if __name__ == "__main__":
    Main()
