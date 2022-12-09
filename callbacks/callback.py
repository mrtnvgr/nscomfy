class Callback:
    def __init__(self, user_id, master):
        self.user_id = user_id
        self.master = master

    def parse(self, update: dict, button_data: list):
        pass
