from aiogram import BaseMiddleware
from typing import Dict, Any, Callable, Awaitable
from aiogram.types import Message
from modules.fabric.UserFabric import CreateUser, UserId

class UserMidleware(BaseMiddleware):
    def __init__(self, path, bot, users):
        self._path = path
        self._bot = bot
        self._users = users

    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: Dict[str, Any]) -> Any:

        user_id = event.from_user.id

        if user_id not in self._users.keys():
            user_info = UserId(self._path, user_id)
            user_fabric = CreateUser(user_info)
            user = user_fabric.factory_method(bot=self._bot)
            self._users[user_id] = user

        data["user"] = self._users[user_id]

        return await handler(event, data)


