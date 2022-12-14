import logging
from urllib.parse import quote_plus

from keyboards.keyboard import Keyboard
from util import checkAccountName


class SettingsAccount(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        if not self.master.ns.checkSession(self.user_id):
            self.ok = False
            return
        api = self.master.ns.sessions[self.user_id]

        self.text = "Настройки аккаунта:"

        self.keyboard.append(["Переименовать", "Удалить"])

        if len(api._students) > 1:
            self.keyboard.append(["Сменить ученика"])

        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):
        if text == "Удалить":

            msg = "Вы точно хотите удалить текущий аккаунт?"

            user = self.master.master.config["users"][self.user_id]
            current_account = user["current_account"]

            callback_data = f"/deleteAccount {quote_plus(current_account)}"

            self.master.askUserAgreement(self.user_id, msg, callback_data)

            return True

        elif text == "Переименовать":

            newName = self.master.askUser(
                self.user_id, "Напишите новое название аккаунта:"
            )

            if not newName:
                return

            if not checkAccountName(newName):
                self.master.tg_api.sendMessage(
                    self.user_id,
                    "Такое имя аккаунта нельзя использовать. Попробуйте что-нибудь другое.",
                )
                return

            logging.info(f"[NS] {self.user_id}: rename account")

            user = self.master.master.config["users"][self.user_id]
            current_account = user["current_account"]

            account = user["accounts"].pop(current_account)

            user["accounts"][newName] = account
            user["current_account"] = newName
            self.master.master.saveConfig()

            self.master.tg_api.sendMessage(
                self.user_id, f'Аккаунт "{current_account}" переименован в "{newName}"'
            )

        elif text == "Сменить ученика":

            if not self.master.ns.checkSession(self.user_id):
                return
            api = self.master.ns.sessions[self.user_id]

            user = self.master.master.config["users"][self.user_id]
            current_account = user["current_account"]

            callback_data = f"/changeAccountStudent {quote_plus(current_account)}"

            buttons = [
                [
                    {
                        "text": student["name"],
                        "callback_data": callback_data,
                    }
                ]
                for student in api._students
            ]

            self.master.tg_api.sendButtons(
                self.user_id, "Выберите нового ученика:", buttons
            )

            return True

        elif text == "Назад":

            self.master.sendKeyboard(self.user_id, "settings")

            return True
