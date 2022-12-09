from callbacks.callback import Callback


class GetFullSchoolInfo(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, _):
        message_id = update["callback_query"]["message"]["message_id"]

        school_info = self.master.ns.getSchoolInfo(self.user_id, full=True)
        if not school_info:
            return True

        self.master.editButtons(
            self.user_id, message_id, school_info, [], parse_mode="HTML"
        )

        return True