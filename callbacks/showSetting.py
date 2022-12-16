import logging

import util
from callbacks.callback import Callback


class ShowSetting(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)
        group = update["callback_query"]["message"]["text"]

        settingType = button_data[0]

        user = self.master.master.config["users"][self.user_id]

        setting = util.SETTINGS_SCHEMA[settingType]
        setting_state = eval(setting["path"])
        setting_state = util.getSwitchEmoji(setting_state)

        text = []

        text.append(group)
        text.append(f'\n<b>{setting["name"]}:\n</b>')
        text.append(f'Описание: {setting["description"]}')

        buttons = [
            {"text": setting_state, "callback_data": f"/toggleSetting {settingType}"}
        ]

        self.master.editButtons(
            self.user_id,
            message_id,
            "\n".join(text),
            buttons,
            parse_mode="HTML",
        )

        logging.info(f'[NS] {self.user_id}: show "{settingType}" setting')

        return True
