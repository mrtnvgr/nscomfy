from callbacks.callback import Callback

import util


class ShowSetting(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, update, button_data):
        message_id = self._getMessageId(update)

        settingType = button_data[0]

        user = self.master.master.config["users"][self.user_id]

        setting = util.SETTINGS_SCHEMA[settingType]
        setting_state = eval(setting["path"])
        setting_state = util.getSwitchEmoji(setting_state)

        text = []

        text.append(f'<b>{setting["name"]}:\n</b>')
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

        # exec(f'{setting["path"]} = not {setting["path"]}')

        return True
