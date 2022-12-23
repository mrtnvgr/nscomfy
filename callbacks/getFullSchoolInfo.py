from callbacks.callback import Callback


class GetFullSchoolInfo(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, _):
        message_id = self._getMessageId(update)

        school_info = self.master.ns.getSchoolInfo(self.user_id, full=True)
        if not school_info:
            return True

        self.master.tg_api.editButtons(self.user_id, message_id, school_info, [])

        return True
