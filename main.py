import asyncio
import json
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import CommandStart
from modules.logger.logger_config import logger
from modules.users.midleware import UserMidleware
from modules.users.Admin import IUser
from modules.fabric.UserFabric import UserId, CreateUser

users = {}
TOKEN = json.load(open("res/conf.json", "r"))["Token"]
path = "res/conf.json"

dp = Dispatcher()
bot = Bot(token=TOKEN)
dp.message.middleware(UserMidleware(path, bot, users))


@dp.message()
async def universal_handler(message: Message, state: FSMContext, user: IUser):
    await user.handle(message, state)


async def main():
    try:
        await dp.start_polling(bot)
    except Exception as exception_name:
        logger.exception("Global exception in main.py", extra={
            "exception_name": exception_name
        })
        pass


if __name__ == "__main__":
    asyncio.run(main())

