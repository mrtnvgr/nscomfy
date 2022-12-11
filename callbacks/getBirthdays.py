from callbacks.callback import Callback


class GetBirthdays(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)

        if not self.master.ns.checkSession(self.user_id):
            self.master.editButtons(
                self.user_id,
                message_id,
                "Перед тем как запросить дни рождения, войдите в аккаунт.",
                [],
            )
            return True

        self.master.editButtons(
            self.user_id,
            message_id,
            "Подождите...",
            [],
        )

        month = button_data[0]

        birthdays = []

        if month != "YEAR":

            birthdays.append(self.master.ns.getBirthdays(self.user_id, month))

        else:

            months = self.master.ns.getBirthdayMonths(self.user_id)
            for month in months.values():

                birthday = self.master.ns.getBirthdays(self.user_id, month)
                birthdays.append(birthday)

        self.master.tg_api.deleteMessage(self.user_id, message_id)

        for birthday in birthdays:
            self.master.tg_api.sendMessage(self.user_id, birthday)

        return True
