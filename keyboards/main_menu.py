from keyboards.keyboard import Keyboard

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
