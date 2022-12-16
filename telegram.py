import callbacks
import keyboards
import util
from ns import NetSchoolSessionHandler
from nsapi import NetSchoolAPI
from tgapi import TelegramAPI


class TelegramHandler:
    def __init__(self, master):
        self.master = master
        self.ns = NetSchoolSessionHandler(self)

        token = self.master.config["telegram"]["token"]
        self.tg_api = TelegramAPI(token)

        # Set offset to latest update
        self.getInstantUpdates()

    def getUpdates(self, limit=100, timeout=60):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.tg_api.getUpdates(offset, limit, timeout)

        if len(updates) > 0:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        return updates

    def getInstantUpdates(self):
        return self.getUpdates(timeout=0)

    def getUpdateText(self):
        update = self.getUpdates(limit=1)

        if update:
            if "message" in update[0]:
                return update[0]["message"].get("text", "")

    def getButtonAnswer(self):
        updates = self.getUpdates(limit=1)
        if updates:
            return self.parseButtonUpdate(updates[0])

    def parseButtonUpdate(self, update, getText=False):

        if update:

            if "callback_query" in update:

                query = update["callback_query"]

                buttons = query["message"]["reply_markup"]["inline_keyboard"]

                data = query["data"]

                for button_row in buttons:

                    for button in button_row:

                        if button["callback_data"] == data:

                            if button["callback_data"].startswith("/button") or getText:
                                return button["text"]
                            else:
                                return button["callback_data"]

    def updateHandler(self, update):
        user_id = str(self.tg_api.getUserIdFromUpdate(update))

        try:

            if user_id not in self.ns.sessions:
                self.addNewUser(user_id)

            if self.menuAnswerHandler(user_id, update):
                return

            # Check if user is currently logged in
            if self.master.config["users"][user_id]["current_account"]:
                self.sendKeyboard(user_id, "mm")

            # Login menu
            if not self.master.config["users"][user_id]["current_account"]:
                self.sendKeyboard(user_id, "account_selection")

        except Exception as ex:
            msg, unknown = self.master.handleError(user_id, ex)
            if unknown:
                self.tg_api.sendMessage(user_id, "Неожиданная ошибка.")
            else:
                self.tg_api.sendMessage(user_id, f"Ошибка: {msg}")

    def menuAnswerHandler(self, user_id, update):

        if "message" in update:
            text = update["message"].get("text", "")

            current_keyboard = self.master.config["users"][user_id]["current_keyboard"]

            if not current_keyboard:
                return

            keyboard_func = keyboards.KEYBOARDS.get(current_keyboard)
            if not keyboard_func:
                return

            keyboard = keyboard_func(user_id, self)

            return keyboard.parse(text)

        elif "callback_query" in update:

            button_data = self.parseButtonUpdate(update)

            if not button_data:
                return

            button_data = button_data.split(" ")

            callback_func = callbacks.CALLBACKS.get(button_data[0])
            if not callback_func:
                return

            callback = callback_func(user_id, self)

            return callback.parse(update, button_data[1:])

    def askForAccount(self, user_id):

        account = {}

        account["url"] = self.askUser(
            user_id,
            "Напишите ссылку на нетгород:"
            "\nНапример: sgo.tomedu.ru"
            "\n(формат ссылки не важен)",
        )
        if not account["url"]:
            return "TIMEOUT"

        try:
            api = NetSchoolAPI(user_id, account["url"])
        except Exception as exception:
            error_msg, _ = self.master.handleError(user_id, exception)
            self.tg_api.sendMessage(user_id, error_msg)
            return

        account["login"] = self.askUser(user_id, "Напишите логин от аккаунта:")
        if not account["login"]:
            return "TIMEOUT"
        account["password"] = self.askUser(user_id, "Напишите пароль от аккаунта:")
        if not account["password"]:
            return "TIMEOUT"

        message_id = self.tg_api.sendMessage(user_id, "Подождите...")["message_id"]

        try:
            districts_response = api.getMunicipalityDistrictList()
            schools_response = api.getSchoolList()
        except Exception as exception:
            error_msg, _ = self.master.handleError(user_id, exception)
            self.editButtons(user_id, message_id, error_msg, [])
            return

        districts = [
            {"text": district["name"], "callback_data": district["id"]}
            for district in districts_response
        ]

        municipalityDistrictId = self.askUserWithButtons(
            user_id, message_id, "Выберите округ:", districts
        )
        if not municipalityDistrictId:
            return "TIMEOUT"

        addresses = list(
            {
                school["addressString"]
                for school in schools_response
                if str(school["municipalityDistrictId"]) == municipalityDistrictId
            }
        )

        account["address"] = self.askUserWithButtons(
            user_id, message_id, "Выберите адрес:", addresses
        )
        if not account["address"]:
            return "TIMEOUT"

        schools = [
            school["name"]
            for school in schools_response
            if school["addressString"] == account["address"]
        ]

        account["school"] = self.askUserWithButtons(
            user_id, message_id, "Выберите школу:", schools
        )
        if not account["school"]:
            return "TIMEOUT"

        self.editButtons(user_id, message_id, "Подождите...", [])

        try:
            api.login(account["login"], account["password"], account["school"])
        except Exception as exception:
            self.handleLoginError(user_id, message_id, exception)
            return

        students = api._students
        student_buttons = [student["name"] for student in students]

        account["student"] = self.askUserWithButtons(
            user_id,
            message_id,
            "Выберите ученика:\n(можно изменить в настройках)",
            student_buttons,
        )
        if not account["student"]:
            return "TIMEOUT"

        api.logout()

        self.editButtons(
            user_id,
            message_id,
            "Напишите название аккаунта (в списке аккаунтов):\n(можно изменить в настройках)",
            [],
        )
        name = self.getUpdateText()
        if not name:
            return "TIMEOUT"

        if not util.checkAccountName(name):
            self.tg_api.sendMessage(
                user_id,
                "Такое имя аккаунта нельзя использовать. Попробуйте что-нибудь другое.",
            )
            return

        user = self.master.config["users"][user_id]

        if name in user["accounts"]:
            msg = "У вас уже есть аккаунт под таким названием."
            if not self.askUserAgreement(user_id, msg, "перезаписи аккаунта"):
                return

        self.addNewUser(user_id)

        user["accounts"][name] = account
        self.master.saveConfig()

        return True

    def addNewUser(self, user_id):
        if user_id not in self.master.config["users"]:
            self.master.config["users"][user_id] = {}
        user = self.master.config["users"][user_id]  # noqa: F841

        params = [
            ("user", "accounts", {}),
            ("user", "current_account", None),
            ("user", "current_keyboard", None),
            ("user", "settings", {}),
        ]

        settings_groups = []
        for setting in util.SETTINGS_SCHEMA.keys():
            group = setting.split(".")[0]
            if group not in settings_groups:
                params.append(('user["settings"]', group, {}))
                settings_groups.append(group)

        for setting_name, setting_data in util.SETTINGS_SCHEMA.items():
            # Получаем место элемента из путя к нему
            # ...["settings"]["setting"] -> ...["settings"]
            dictionary = "[".join(setting_data["path"].split("[")[:-1])

            key = setting_name.split(".")[-1]
            default_value = setting_data["default_value"]
            params.append((dictionary, key, default_value))

        new = False

        for dictionary, key, default_value in params:
            old_value = eval(f"{dictionary}.setdefault(key, default_value)")
            if old_value == default_value:
                new = True

        if new:
            self.master.saveConfig()

    def askUser(self, user_id, msg):
        self.tg_api.sendMessage(user_id, msg)

        return self.getUpdateText()

    def askUserWithButtons(self, user_id, message_id, msg, buttons):

        if type(buttons) is list:
            if len(buttons) == 1:
                return buttons[0]

        self.editButtons(user_id, message_id, msg, buttons)
        return self.getButtonAnswer()

    def askUserAgreement(self, user_id, reason="", action="продолжения"):
        message = f'Для {action} напишите "Согласен":'

        if reason:
            message = f"{reason}\n{message}"

        userAnswer = self.askUser(user_id, message)
        if userAnswer == "Согласен":
            return True

    def sendKeyboard(self, user_id, ktype):
        """Send different keyboards to user"""

        keyboard_func = keyboards.KEYBOARDS[ktype]
        keyboard = keyboard_func(user_id, self)

        if keyboard.ok:

            self.tg_api.sendKeyboard(user_id, keyboard.text, keyboard.data)

            self.master.config["users"][user_id]["current_keyboard"] = ktype
            self.master.saveConfig()

    def sendButtons(self, user_id, text, values, **kwargs):

        markup = self._parseButtons(values)

        return self.tg_api.sendButtons(user_id, text, markup, **kwargs)

    def editButtons(self, user_id, message_id, text, values, **kwargs):

        markup = self._parseButtons(values)

        return self.tg_api.editButtons(user_id, message_id, text, markup, **kwargs)

    def editMessageReplyMarkup(self, user_id, message_id, values):
        markup = self._parseButtons(values)
        return self.tg_api.editMessageReplyMarkup(user_id, message_id, markup)

    def handleLoginError(self, user_id, message_id, exception, pop: str = ""):

        error_msg, unknown_err = self.master.handleError(user_id, exception)

        self.editButtons(user_id, message_id, error_msg, [])
        if pop and not unknown_err:
            self.master.config["users"][user_id]["accounts"].pop(pop)
            self.master.saveConfig()

    def forceLogout(self, user_id):
        self.ns.logout(user_id)
        self.master.config["users"][user_id]["current_account"] = None
        self.master.saveConfig()

    @staticmethod
    def _parseButtons(values):
        buttons = []

        ind = 0
        for value in values:
            if type(value) is str:
                buttons.append([{"text": value, "callback_data": f"/button {ind}"}])
            elif type(value) is dict:
                buttons.append([value])
            elif type(value) is list:
                if type(value[0]) is dict:
                    buttons.append(value)
                else:
                    values = []
                    for button in value:
                        ind += 1
                        values.append(
                            {"text": button, "callback_data": f"/button {ind}"}
                        )
                    buttons.append(values)
            ind += 1

        return {"inline_keyboard": [*buttons]}
