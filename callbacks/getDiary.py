from callbacks.callback import Callback

import logging


class GetDiary(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)

        if not self.master.ns.checkSession(self.user_id):
            self.master.editButtons(
                self.user_id,
                message_id,
                "Перед тем как запросить дневник, войдите в аккаунт.",
                [],
            )
            return True

        diary_kwargs = {}

        text = button_data[0]
        dateanswer = button_data[1]

        if text == "Расписание":
            diary_kwargs["show_tasks"] = False
            diary_kwargs["show_marks"] = False
        elif text == "Задания":
            diary_kwargs["only_tasks"] = True
        elif text == "Оценки":
            diary_kwargs["only_marks"] = True

        logging.info(f'[NS] {self.user_id}: "{text}" diary request')

        self.master.editButtons(self.user_id, message_id, "Подождите...", [])

        diary = self.master.ns.getDiary(self.user_id, dateanswer, **diary_kwargs)
        if not diary:
            self.master.tg_api.deleteMessage(self.user_id, message_id)
            return True

        self.master.tg_api.deleteMessage(self.user_id, message_id)

        for day in diary:
            text, buttons = day

            self.master.sendButtons(self.user_id, text, buttons, parse_mode="HTML")

        return True
