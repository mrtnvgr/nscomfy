from keyboards.keyboard import Keyboard

import logging


class Info(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Аккаунт", "Школа"])
        self.keyboard.append(["Дни рождения", "Бот"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False

    def parse(self, text):

        if text == "Школа":

            logging.info(f"[NS] {self.user_id}: school info request")

            school_info = self.master.ns.getSchoolInfo(self.user_id, full=False)
            if school_info:

                buttons = [
                    {
                        "text": "Получить полные данные",
                        "callback_data": "/getFullSchoolInfo",
                    }
                ]

                self.master.sendButtons(self.user_id, school_info, buttons)

            return True

        elif text == "Аккаунт":

            logging.info(f"[NS] {self.user_id}: account info request")

            account_info = self.master.ns.getAccountInfo(self.user_id)

            user_photo = self.master.ns.getUserPhoto(self.user_id)

            if account_info:
                self.master.tg_api.editPhoto(
                    self.user_id,
                    user_photo,
                    account_info,
                    parse_mode="HTML",
                )

            return True

        elif text == "Бот":

            logging.info(f"[NS] {self.user_id}: bot info request")

            text = []

            users = self.master.master.config["users"]

            userCount = len(users)

            accCount = 0
            for user in users:
                accounts = users[user]["accounts"]
                accCount += len(accounts)

            giturl = "github.com/mrtnvgr/nscomfy"
            text.append("<b>Контакты:</b>")
            text.append("Автор: @mrtnvgr")
            text.append(f"Страница проекта: {giturl}")

            text.append("\n<b>Статистика:</b>")
            text.append(f"Количество пользователей: <b>{userCount}</b>")
            text.append(f"Количество аккаунтов: <b>{accCount}</b>")

            self.master.tg_api.sendMessage(
                self.user_id,
                "\n".join(text),
                params={"disable_web_page_preview": True},
            )

            return True

        elif text == "Дни рождения":

            message_id, birthdays = self.master.ns.getBirthdays(self.user_id)
            self.master.editButtons(
                self.user_id, message_id, birthdays, [], parse_mode="HTML"
            )

            return True
