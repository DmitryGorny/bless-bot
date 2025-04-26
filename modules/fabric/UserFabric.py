import json
from abc import ABC, abstractmethod

from aiogram import Dispatcher, Bot

from modules.users.Admin import IUser, Admin
from modules.users.User import User

class UserId:
    def __init__(self, path: str, user_id: int):
        self.__file_path = path
        self.__user_id = user_id

    def get_id(self):
        with open(self.__file_path, "r", encoding="utf-8") as f:
            users = json.load(f)
            if users["AdminId"] == self.__user_id:
                return ["admin", users["AdminId"]]
            return ["user", users["AdminId"]]

class Fabric(ABC):
    @abstractmethod
    def factory_method(self, **kwargs) -> IUser:
        pass


class CreateUser(Fabric):
    def __init__(self, UserId: UserId):
        self.__UserId = UserId

    def factory_method(self, **kwargs) -> IUser:
        role = self.__UserId.get_id()

        if role[0] == "admin":
            return Admin()
        else:
            bot = kwargs.get("bot")
            return User(bot, role[1])

