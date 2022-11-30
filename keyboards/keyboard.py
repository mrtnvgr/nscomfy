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
