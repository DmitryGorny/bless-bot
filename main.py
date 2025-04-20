import asyncio
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from modules.logger.logger_config import logger

from modules.fabric.UserFabric import UserId, CreateUser


TOKEN = json.load(open("res/conf.json", "r"))["Token"]
path = "res/conf.json"

dp = Dispatcher()
bot = Bot(token=TOKEN)


@dp.message(CommandStart())
async def route_user(message: Message):
    user_id = UserId(path, message.from_user.id)
    user_fabric = CreateUser(user_id)
    user = user_fabric.factory_method(dp=dp, bot=bot)
    await user.start(message)


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

