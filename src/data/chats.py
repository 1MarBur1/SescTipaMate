class ChatDataStorage:
    def __init__(self):
        with open("ids.txt") as file:
            self.joined_chats = {int(i[0]): {
                "group": int(i[1]),
                "mail": i[2] == "True",
                "pin": i[3] == "True",
                "pinned_message": int(i[4]),
                "news": i[5] == "True"
            } for i in [line.split(",") for line in file.readlines()]}

    def has_chat(self, chat_id):
        return chat_id in self.joined_chats

    def get_chat_data(self, chat_id):
        return self.joined_chats.get(chat_id, {})

    def set_chat_data(self, chat_id, data):
        if not self.has_chat(chat_id):
            self.joined_chats[chat_id] = {}
        self.joined_chats[chat_id].update(data)


database = ChatDataStorage()
