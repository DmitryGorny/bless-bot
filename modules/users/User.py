import aiogram.exceptions
from aiogram import F

from .Admin import IUser
import json
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.context import FSMContext
from modules.order.Order import OrderBuilder, Order
from modules.logger.logger_config import logger


class MakeOrder(StatesGroup):
    order = State()
    photo = State()


class User(IUser):
    def __init__(self, bot, id):
        self._positions = []
        self._orderBuilder = OrderBuilder()
        self._bot = bot
        self.__admin_id = id
        self._user_link = None

        self.__commands = { #сюда записывать только комнады, fsm проверять в handle
            "Сделать заказ": self.start_input_process #переписать все к хуям
        }

    def get_postions(self):
       self._positions = []
       with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)
            for i in dataF["positions"]:
                self._positions.append(i)

    async def handle(self, message: Message, state: FSMContext):
        if message.text == "/start":
            await self.start(message)
            return

        if message.text not in self.__commands:
            current_state = await state.get_state()
            if current_state == MakeOrder.order.state:
                await self.process_input(message, state)
            elif current_state == MakeOrder.photo.state:
                await self.set_photo(message, state)
            else:
                await message.answer("Неизвестная команда, используйте кнопки или /start")
        else:
            await self.__commands[message.text](message, state)

    async def start(self, message:Message):
        with open("res/welcome.conf", "r", encoding="utf-8") as file:
            welcome = file.read()

        if len(welcome) == 0:
            welcome = "Начало"
        await message.answer(welcome, reply_markup=self.create_buttons())
        print(message.from_user.username)
        self._user_link = f"https://t.me/{message.from_user.username}"

    def create_buttons(self):
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Сделать заказ")]
        ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")
        return kb

    async def start_input_process(self, message: Message, state: FSMContext):
         self._orderBuilder.order = Order()
         await message.answer("Последовательно отвечайте на вопросы")
         await state.set_state(MakeOrder.order)

         with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)
            await message.answer(dataF["positions"][0])

         await state.update_data(
            fields=dataF["positions"],
            current_step=0,
            answers={}
         )

    async def process_input(self, message: Message, state: FSMContext):
        if self._user_link is None:
            self._user_link = f"https://t.me/{message.from_user.username}"
        data = await state.get_data()
        current_step = data["current_step"]
        fields = data["fields"]

        current_field = fields[current_step]
        data["answers"][current_field] = message.text
        self._orderBuilder.add_position(message.text)
        if current_step + 1 < len(fields):
            await state.update_data(
                current_step=current_step + 1,
                answers=data["answers"]
            )
            next_field = fields[current_step + 1]
            await message.answer(f"Введите {next_field}:")
        else:
            await message.answer("Теперь нужно отправить фото товара (без него заказ не будет создан)\n")
            await state.set_state(MakeOrder.photo)

    async def set_photo(self, message: Message, state: FSMContext):
        try:
            photo = message.photo[-1]
        except TypeError:
            await message.answer("Нужно прислать фото")
            logger.exception("Handled exception in User", extra={
                    "exception": "User didnt send photo",
                    "user_id": message.from_user.id,
                    "user_name": message.from_user.username
                })
            return
        file_info = await self._bot.get_file(photo.file_id)

        file_path = f"res/img/{photo.file_id}.jpg"
        self._orderBuilder.add_photo(file_path)
        await self._bot.download_file(file_info.file_path, destination=file_path)

        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Связаться с менеджером", url="https://t.me/blesssmanager")]
        ])

        await message.answer("Фото получено и сохранено!")
        await message.answer("Заказ был отправлен менеджеру, ожидайте ответа. Спасибо!", reply_markup=inline_kb)
        await state.clear()

        await self.send_order()

    async def send_order(self):
        order = self._orderBuilder.order
        orderPositions = ""
        for i in order.positions:
            orderPositions += i + "\n"

        photo = FSInputFile(order.photo[0]) #Попытаться отослать фото с сообщением
        try:
            await self._bot.send_photo(chat_id=self.__admin_id, photo=photo, caption=f"""Заказ от {self._user_link}\n{orderPositions}""")
        except aiogram.exceptions.TelegramBadRequest:
            logger.exception("Handled exception in User", extra={
                "exception": "Chat_not_found",
            })
