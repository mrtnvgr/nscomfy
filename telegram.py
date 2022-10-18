from api import TelegramAPI

class TelegramHandler:
    
    def __init__(self, master):
        self.master = master

        token = self.master.config["telegram"]["token"]
        self.telegram_api = TelegramAPI(token)

    def getUpdates(self):

        offset = self.master.config["telegram"].get("offset", 0)
        updates = self.telegram_api.getUpdates(offset)

        if updates != []:

            offset = int(updates[-1]["update_id"]) + 1
            self.master.config["telegram"]["offset"] = offset
            self.master.saveConfig()

        for update in updates:
            
            user_id = update["message"]["chat"]["id"]
            self.telegram_api.sendMessage(user_id, user_id)
