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

        firstRow = ["Дневник"]

        self.master.ns.setOverdueCount(self.user_id)
        if api._overdue_count > 0:
            overdueCount = f"\nТочки: {api._overdue_count}"
            firstRow.append("Точки")
        else:
            overdueCount = ""

        if api._unreaded_mail_messages > 0:
            unreaded = api._unreaded_mail_messages
            unreaded = f"\nНепрочитанные письма: {unreaded}"
        else:
            unreaded = ""

        studentText = f"{student_info}{overdueCount}{unreaded}"

        self.text = f"<b>Главное меню</b>\n\n{studentText}\n\n"

        self.keyboard.append(firstRow)
        self.keyboard.append(["Информация"])
        self.keyboard.append(["Настройки", "Выйти"])

        self.one_time_keyboard = False

    def parse(self, text):

        if text == "Выйти":

            self.master.forceLogout(self.user_id)

        elif text == "Точки":

            days = self.master.ns.getOverdueTasks(self.user_id)
            if days:
                for day in days:
                    self.master.tg_api.sendMessage(self.user_id, day)
            else:
                self.master.tg_api.sendMessage(self.user_id, "Нету! :3")
            return True

        elif text == "Дневник":

            self.master.sendKeyboard(self.user_id, "diary")
            return True

        elif text == "Настройки":

            self.master.sendKeyboard(self.user_id, "settings")
            return True

        elif text == "Информация":

            self.master.sendKeyboard(self.user_id, "info")
            return True
