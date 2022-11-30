from keyboards.keyboard import Keyboard

class SettingsAccount(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def set(self):
        if not self.master.ns.checkSession(self.user_id):
            self.ok = False
            return
        api = self.master.ns.sessions[self.user_id]

        self.text = "Настройки аккаунта:"

        self.keyboard.append(["Переименовать", "Удалить"])

        if len(api._students) > 1:
            self.keyboard.append(["Сменить ученика"])

        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False
