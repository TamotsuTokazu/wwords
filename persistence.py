from telegram.ext import BasePersistence, PersistenceInput
import pickle

class MyPersistence(BasePersistence):
    def __init__(self, filename, store_data: PersistenceInput = PersistenceInput(user_data=True), update_interval: float = 60):
        super().__init__(store_data, update_interval)
        self.filename = filename
        try:
            with open(filename, 'rb') as f:
                self.d = pickle.load(f)
        except:
            self.d = dict()

    async def flush(self) -> None:
        for k in self.d:
            try:
                del self.d[k]['game']
            except KeyError:
                pass
        with open(self.filename, 'wb') as f:
            pickle.dump(self.d, f)

    async def drop_chat_data(self, chat_id: int) -> None:
        pass

    async def drop_user_data(self, user_id: int) -> None:
        try:
            del self.d[user_id]
        except KeyError:
            pass

    async def get_bot_data(self) -> None:
        return dict()

    async def get_callback_data(self) -> None:
        pass

    async def get_chat_data(self) -> None:
        return dict()

    async def get_conversations(self) -> None:
        return dict()

    async def get_user_data(self) -> None:
        return self.d

    async def refresh_bot_data(self, bot_data) -> None:
        pass

    async def refresh_chat_data(self, chat_id: int, chat_data) -> None:
        pass

    async def refresh_user_data(self, user_id: int, user_data: dict) -> None:
        pass

    async def update_bot_data(self, data) -> None:
        pass

    async def update_callback_data(self, data) -> None:
        pass

    async def update_chat_data(self, chat_id: int, data) -> None:
        pass

    async def update_conversation(self, name: str, key, new_state) -> None:
        pass

    async def update_user_data(self, user_id: int, data: dict) -> None:
        self.d[user_id] = data