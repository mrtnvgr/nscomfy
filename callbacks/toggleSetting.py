import logging

import util
from callbacks.callback import Callback


class ToggleSetting(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)

        setting_type = button_data[0]

        setting = util.SETTINGS_SCHEMA[setting_type]

        user = self.master.master.config["users"][self.user_id]
        exec(f'{setting["path"]} = not {setting["path"]}')
        self.master.master.saveConfig()

        setting_state = eval(setting["path"])
        setting_state = util.getSwitchEmoji(setting_state)

        logging.info(f'[NS] {self.user_id}: toggle "{setting_type}" setting')

        buttons = [
            {"text": setting_state, "callback_data": f"/toggleSetting {setting_type}"}
        ]

        self.master.editMessageReplyMarkup(
            self.user_id,
            message_id,
            buttons,
        )

        return True
