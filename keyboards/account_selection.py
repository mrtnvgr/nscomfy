import logging

from keyboards.keyboard import Keyboard


class AccountSelection(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = (
            "Чтобы начать работу добавьте свой аккаунт или выберите из существующих:"
        )

        users = self.master.master.config["users"]
        accounts = users[self.user_id]["accounts"]
        for name in sorted(accounts):
            self.keyboard.append([name])

        self.keyboard.append(["Добавить аккаунт"])

    def parse(self, text):
        if text == "Добавить аккаунт":

            logging.info(f"[NS] {self.user_id}: add account")

            status = self.master.askForAccount(self.user_id)
            if status == "TIMEOUT":
                self.master.tg_api.sendMessage(
                    self.user_id,
                    "Ваше отведённое время на ответ истекло. Попробуйте еще раз.",
                )
            return

        user = self.master.master.config["users"][self.user_id]
        accounts = user["accounts"]

        if text not in accounts:
            self.master.tg_api.sendMessage(
                self.user_id,
                "Такого аккаунта не существует."
                "Для выбора аккаунта используйте кнопки клавиатуры телеграмма.",
            )
            return

        message_id = self.master.tg_api.sendMessage(self.user_id, "Подождите...")[
            "message_id"
        ]
        account = accounts[text]
        try:
            self.master.ns.login(
                self.user_id,
                account["url"],
                account["login"],
                account["password"],
                account["student"],
                account["school"],
            )
        except Exception as ex:
            self.master.handleLoginError(
                self.user_id,
                message_id,
                ex,
                pop=text,
            )
            return

        user["current_account"] = text
        self.master.master.saveConfig()

        self.master.tg_api.deleteMessage(self.user_id, message_id)
