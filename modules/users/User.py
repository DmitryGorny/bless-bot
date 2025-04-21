import aiogram.exceptions
from aiogram import F

from .Admin import IUser
import json
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.context import FSMContext
from modules.order.Order import OrderBuilder, Order
from modules.logger.logger_config import logger


class MakeOrder(StatesGroup):
    order = State()
    photo = State()


class User(IUser):
    def __init__(self, dp, bot, id):
        self._dp = dp
        self._register_handlers()
        self._positions = []
        self._orderBuilder = OrderBuilder()
        self._bot = bot
        self.__admin_id = id
        self._user_link = None

    def get_postions(self):
       self._positions = []
       with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)
            for i in dataF["positions"]:
                self._positions.append(i)

    def _register_handlers(self):
        self._dp.message.register(self.start, CommandStart())
        self._dp.message.register(self.start_input_process, F.text == "Сделать заказ")
        self._dp.message.register(self.process_input, MakeOrder.order)
        self._dp.message.register(self.set_photo, MakeOrder.photo)

    async def start(self, message:Message):
        with open("res/welcome.conf", "r", encoding="utf-8") as file:
            welcome = file.read()

        if len(welcome) == 0:
            welcome = "Начало"
        await message.answer(welcome, reply_markup=self.create_buttons())
        self._user_link = f"https://t.me/{message.from_user.username}"
        self.get_postions()

    def create_buttons(self):
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Сделать заказ")]
        ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")
        return kb

    async def start_input_process(self, message: Message, state: FSMContext):
         self._orderBuilder.order = Order()
         await message.answer("Последовательно отвечайте на вопросы")
         await state.set_state(MakeOrder.order)
         await message.answer(self._positions[0])

         await state.update_data(
            fields=self._positions,
            current_step=0,
            answers={}
         )

    async def process_input(self, message: Message, state: FSMContext):
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

        await message.answer("Фото получено и сохранено!")
        await message.answer("Заказ был отправлен менеджеру, ожидайте ответа. Спасибо!")
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
