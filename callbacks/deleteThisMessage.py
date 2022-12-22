from callbacks.callback import Callback


class DeleteThisMessage(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, _):
        message_id = self._getMessageId(update)
        self.master.tg_api.deleteMessage(self.user_id, message_id)
        return True
