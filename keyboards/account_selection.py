from keyboards.keyboard import Keyboard

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
