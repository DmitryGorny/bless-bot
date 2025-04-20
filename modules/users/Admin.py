import json
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    FSInputFile
from aiogram.fsm.context import FSMContext
from abc import ABC, abstractmethod

from modules.logger.logger_config import logger


class Positions(StatesGroup):
    single_position = State()
    postions = State()
    number_of_postions = State()
    welcome_text = State()

class IUser(ABC):
    @abstractmethod
    def _register_handlers(self) -> None:
        pass

    @abstractmethod
    async def start(self, message:Message) -> None:
        pass

    @abstractmethod
    def create_buttons(self) -> None:
        pass

    @abstractmethod
    def get_postions(self) -> None:
        pass

    @abstractmethod
    async def start_input_process(self) -> None:
        pass

    @abstractmethod
    async def process_input(self) -> None:
        pass

class Admin(IUser):
    def __init__(self, dp:Dispatcher):
        self._dp = dp
        self._register_handlers()

    def _register_handlers(self):
        self._dp.message.register(self.start, Command("dsfdsfdsds"))

        self._dp.message.register(self.send_logs, F.text == "Скинуть файл с логами")

        self._dp.message.register(self.add_position, F.text == "Добавить вопрос")
        self._dp.message.register(self.singe_postion_added, Positions.single_position)

        self._dp.message.register(self.add_postions, F.text == "Ввести вопросы заново")
        self._dp.message.register(self.start_input_process, Positions.number_of_postions)
        self._dp.message.register(self.process_input, Positions.postions)

        self._dp.message.register(self.get_postions, F.text == "Просмотреть анкету")
        self._dp.callback_query.register(self.start, lambda callback: callback.data == "stop_welcome")
        self._dp.message.register(self.create_welcome, F.text == "Изменить текст приветствия")
        self._dp.message.register(self.write_welcome, Positions.welcome_text)


    async def send_logs(self, message: Message):
        doc = FSInputFile("modules/logger/logs/bot.log")
        await message.answer_document(doc)

    def create_buttons(self):
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Ввести вопросы заново")], [KeyboardButton(text="Добавить вопрос")],
            [KeyboardButton(text="Просмотреть анкету")], [KeyboardButton(text="Изменить текст приветствия")],
            [KeyboardButton(text="Скинуть файл с логами")]
        ], resize_keyboard=True, input_field_placeholder="Выберите пункт меню")
        return kb

    async def create_welcome(self, message:Message, state: FSMContext):
        await state.set_state(Positions.welcome_text)
        with open("res/welcome.conf", "r", encoding="utf-8") as welcome:
            welcome = welcome.read()
        if len(welcome) == 0:
            welcome = "Начало"
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data="stop_welcome")]
        ])

        await message.answer(f"Ваше нынешнее приветсвие:\n{welcome}\n--------------------\nВведите новое приветствие:", reply_markup=inline_kb)

    async def write_welcome(self, message: Message, state: FSMContext):
        await state.update_data(welcome=message.text)
        print(message.text)
        with open("res/welcome.conf", "w", encoding="utf-8") as welcome:
            try:
                welcome.write(message.text)
            except TypeError:
                logger.exception("Handled exception in Admin.py", extra={
                    "exception": "Admin entered photo instead of str",
                })
                await message.answer("Введите текст")
                return

        await message.answer("Успешно записано")
        await state.clear()

    async def start(self, message:Message):
        await message.answer("Начало", reply_markup=self.create_buttons())

    async def add_position(self, message:Message, state: FSMContext):
        await state.set_state(Positions.single_position)
        await message.answer("Введите вопрос")

    async def singe_postion_added(self, message:Message, state: FSMContext):
        await state.update_data(postion=message.text)
        data = await state.get_data()
        await state.clear()
        await message.answer(f"Вопрос добавлен\n '{message.text}'")

        with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)

            with open("res/postions.json", "w+") as positions:
                for key in data.keys():
                    dataF["positions"].append(data[key])

                positions.write(json.dumps(dataF))

    async def add_postions(self, message: Message, state: FSMContext):
        await message.answer("Введите количество вопросов")
        await state.set_state(Positions.number_of_postions)

    async def start_input_process(self, message: Message, state: FSMContext):
        try:
            number = int(message.text)
        except ValueError:
            await message.answer("Вы ввели строковое значение, а надо числовое")
            logger.exception("Handled exception in Admin.py", extra={
                    "exception": "Admin entered str instead of int",
                    "user_id": message.from_user.id,
                    "user_name": message.from_user.username
            })
            return

        with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)
            with open("res/postions.json", "w+") as positions:
                dataF["positions"].clear()
                positions.write(json.dumps(dataF))

        await state.update_data(number_of_postions=message.text)
        await state.set_state(Positions.postions)

        listOfPostions = []
        for i in range(number):
            listOfPostions.append("Вопрос {}".format(i+1))

        await state.update_data(
            fields=listOfPostions,
            current_step=0,
            answers={}
        )

        await message.answer(f"Введите {listOfPostions[0]}:")

    async def process_input(self, message: Message, state: FSMContext):
        data = await state.get_data()
        current_step = data["current_step"]
        fields = data["fields"]

        current_field = fields[current_step]
        data["answers"][current_field] = message.text

        with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)

            with open("res/postions.json", "w+") as positions:
                dataF["positions"].append(message.text)

                positions.write(json.dumps(dataF))

        if current_step + 1 < len(fields):
            await state.update_data(
                current_step=current_step + 1,
                answers=data["answers"]
            )
            next_field = fields[current_step + 1]
            await message.answer(f"Введите {next_field}:")
        else:
            await message.answer(
                "Спасибо! Ваши данные:\n" +
                "\n".join(f"{k}: {v}" for k, v in data["answers"].items()),
            )
            await state.clear()

    async def get_postions(self, message: Message):
         with open("res/postions.json", 'r', encoding='utf-8') as file:
            dataF = json.load(file)
            for i in dataF["positions"]:
                await message.answer(i)


