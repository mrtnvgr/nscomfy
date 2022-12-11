from callbacks.callback import Callback


class GetBirthdays(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = update["callback_query"]["message"]["message_id"]

        if not self.master.ns.checkSession(self.user_id):
            self.master.editButtons(
                self.user_id,
                message_id,
                "Перед тем как запросить дни рождения, войдите в аккаунт.",
                [],
            )
            return True

        month = button_data[0]

        birthdays = self.master.ns.getBirthdays(self.user_id, month)
        self.master.editButtons(
            self.user_id, message_id, birthdays, [], parse_mode="HTML"
        )
