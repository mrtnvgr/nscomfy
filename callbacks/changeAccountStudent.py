import logging
from urllib.parse import unquote_plus

from callbacks.callback import Callback


class ChangeAccountStudent(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        button_data = [unquote_plus(data) for data in button_data]
        message_id = self._getMessageId(update)
        new_student = self.master.parseButtonUpdate(update, getText=True)

        if not self.master.ns.checkSession(self.user_id):
            self.master.tg_api.editButtons(
                self.user_id,
                message_id,
                f'Для корректной работы данной кнопки, войдите в аккаунт "{button_data[0]}".',
                [],
            )
            return True
        api = self.master.ns.sessions[self.user_id]

        user = self.master.master.config["users"][self.user_id]
        current_account = user["current_account"]

        if current_account != button_data[0]:
            self.master.tg_api.editButtons(
                self.user_id,
                message_id,
                "Смена ученика одного аккаунта под другим может вызвать ошибки."
                f'\nДля корректной работы данной кнопки, войдите в аккаунт "{button_data[0]}".',
                [],
            )
            return True

        accountStudents = [student["name"] for student in api._students]
        if new_student not in accountStudents:
            self.master.tg_api.editButtons(
                self.user_id,
                message_id,
                "Такого ученика больше не существует."
                "\nПопробуйте вызвать это меню еще раз.",
                [],
            )
            return True

        logging.info(f"[NS] {self.user_id}: change account student")

        user["accounts"][current_account]["student"] = new_student
        self.master.master.saveConfig()

        self.master.tg_api.editButtons(
            self.user_id,
            message_id,
            f'Ученик аккаунта "{current_account}" сменён на "{new_student}"'
            "\nДля продолжения работы под новым учеником, войдите в аккаунт еще раз.",
            [],
        )

        self.master.forceLogout(self.user_id)
