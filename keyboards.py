class Keyboard:
    def __init__(self, user_id, master):
        self.user_id = user_id
        self.master = master

        self.ok = True

        self.keyboard = []
        self.one_time_keyboard = True
        self.resize_keyboard = True
        self.text = ""

        self.set()

        self.data = {
            "keyboard": self.keyboard,
            "one_time_keyboard": self.one_time_keyboard,
            "resize_keyboard": self.resize_keyboard,
        }

    def set(self):
        pass


class AccountSelection(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите аккаунт:"

        users = self.master.master.config["users"]
        accounts = users[self.user_id]["accounts"]
        for name in sorted(accounts):
            self.keyboard.append([name])

        self.keyboard.append(["Добавить аккаунт"])


class MainMenu(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        if not self.master.ns.checkSession(self.user_id):
            self.ok = False
            return
        api = self.master.ns.sessions[self.user_id]

        student_info = f"Ученик: {api.student_info['name']}"
        activeSessions = f"Пользователей в сети: {len(api._active_sessions)}"

        firstRow = ["Дневник"]

        self.master.ns.setOverdueCount(self.user_id)
        if api._overdue_count > 0:
            overdueCount = f"\nТочки: {api._overdue_count}"
            firstRow.append("Точки")
        else:
            overdueCount = ""

        if api._unreaded_mail_messages > 0:
            unreaded = f"\nНепрочитанные письма: {api._unreaded_mail_messages}"
        else:
            unreaded = ""

        self.text = f"Главное меню\n\n{student_info}{overdueCount}{unreaded}\n\n{activeSessions}"

        self.keyboard.append(firstRow)
        self.keyboard.append(["Информация"])
        self.keyboard.append(["Настройки", "Выйти"])

        self.one_time_keyboard = False


class Diary(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Всё"])
        self.keyboard.append(["Расписание"])
        self.keyboard.append(["Задания", "Оценки"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False


class Settings(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Настройки:"

        self.keyboard.append(["Аккаунт"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False


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


class Info(Keyboard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self):
        self.text = "Выберите тип информации:"

        self.keyboard.append(["Аккаунт", "Школа"])
        self.keyboard.append(["Бот"])
        self.keyboard.append(["Назад"])

        self.one_time_keyboard = False


KEYBOARDS = {
    "account_selection": AccountSelection,
    "mm": MainMenu,
    "diary": Diary,
    "settings": Settings,
    "settings_account": SettingsAccount,
    "info": Info,
}
