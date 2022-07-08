from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import message, reply_keyboard
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.helper import Helper, HelperMode, ListItem
from cgitb import text
import logging, sqlite3, aiogram, datetime, asyncio, random, keyboard
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


db = sqlite3.connect("baza.db")
sql = db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS events (
id INTEGER PRIMARY KEY AUTOINCREMENT,
open INT,
name TEXT,
time TEXT,
comment TEXT,
place TEXT
)""")

sql.execute("""CREATE TABLE IF NOT EXISTS users (
user INT,
events TEXT
)""")
db.commit()

bot = Bot(token='5428307171:AAEDLW3LbtefPwNezErwG_bxtodXGxuxoPM')

dp = Dispatcher(bot, storage=MemoryStorage())

cb = CallbackData("id", "text")


class CreateEvent(StatesGroup):
    event = State()
    time = State()
    place = State()
    comment = State()




@dp.message_handler(Command("start"), state=None)
async def welcome(message):
    if message.from_user.id == message.chat.id:
        sql.execute(f"SELECT * FROM users WHERE user = {message.from_user.id}")
        if sql.fetchone() is None:
            sql.execute(f"INSERT INTO users VALUES (?,?)", (message.from_user.id, 'None'))
            db.commit()
        else:
            await message.answer(f"привет, {message.from_user.first_name}, это events bot", reply_markup=keyboard.start, parse_mode='Markdown')
    elif message.from_user.id != message.chat.id:
        sql.execute(f"SELECT * FROM users WHERE user = {message.from_user.id}")
        if sql.fetchone() is None:
            await message.reply("похоже что ты не зарегестрирован в events bot\nнапиши /start в личные сообщения боту")
        else:
            await message.answer(f"привет, {message.from_user.first_name}, я events bot",parse_mode='Markdown')


@dp.message_handler(state=CreateEvent.event)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        global e_name
        e_name = message.text
        await state.finish()
        await message.answer("Напиши число ивента (например: 17.07 18:00")
        await CreateEvent.time.set()

@dp.message_handler(state=CreateEvent.time)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(datetime.datetime.now())
        global e_time
        e_time = message.text
        await state.finish()
        await message.answer("Где будет проиходить ивент?")
        await CreateEvent.place.set()

@dp.message_handler(state=CreateEvent.place)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        global e_place
        e_place = message.text
        await state.finish()
        await message.answer("Напиши комментарий к ивенту")
        await CreateEvent.comment.set()

@dp.message_handler(state=CreateEvent.comment)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        global e_place
        global e_name
        global e_time
        e_id = random.randint(0, 9999)
        e_comment = message.text
        await state.finish()
        await message.answer(f"📢 ивент - {e_name} \n дата: {e_time} \n место: {e_place} \n комментарий: {e_comment}")
        sql.execute(f"INSERT INTO events VALUES ({e_id}, {1}, ?,?,?,?)", (e_name, e_time, e_comment, e_place))
        db.commit()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('info_'))
async def check(call: types.CallbackQuery):
    event_id = call.data[call.data.find("_") + 1 : ]
    print(event_id)
    for info in sql.execute(f"SELECT * FROM events WHERE id = {event_id}"):
        isgo = types.InlineKeyboardMarkup()
        igo = types.InlineKeyboardButton('я пойду', callback_data=f'isgo_{info[0]}')
        isgo.insert(igo)
        desc_event = f'тусовка - {info[2]} \n {info[3]}  \n place: {info[5]} \n комментарий: {info[4]} \n event_id: {info[0]}'
        await call.message.answer(desc_event, reply_markup=isgo)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('isgo_'))
async def check(call: types.CallbackQuery):
    event_id = call.data[call.data.find("_") + 1:]
    sql.execute(f"UPDATE users SET events = {event_id} WHERE user = {call.from_user.id} ")
    db.commit()
    await call.message.answer('записал тебя в базу данных :)', reply_markup=keyboard.start)

@dp.message_handler(content_types=['text'])
async def main(message : types.Message):
    if message.text == 'ивенты':
        for i in sql.execute(f"SELECT events FROM users WHERE user = {message.from_user.id}"):
            some_events = i
            print(some_events[0])
            if some_events[0] != 'None':
                for i in sql.execute(f"SELECT name FROM events WHERE id = {some_events[0]}"):
                    await message.answer(f"привет, {message.from_user.first_name}, твои ивенты - {i[0]}", reply_markup=keyboard.events_func, parse_mode='Markdown')
            else:
                await message.answer(f"привет, {message.from_user.first_name}, у тебя нету активных ивентов", reply_markup=keyboard.events_func, parse_mode='Markdown')
    if message.text == 'settings':
        await message.answer(f"{message.from_user.first_name}, настройки", reply_markup=keyboard.settings, parse_mode='Markdown')
    if message.text == 'back to menu':
        await message.answer(f"привет, {message.from_user.first_name}, я events bot", reply_markup=keyboard.start, parse_mode='Markdown')

    if message.text == "создать ивент":
        await message.answer("Хорошо, напиши название ивента")
        await CreateEvent.event.set()

    if message.text == 'общие ивенты':
        # some gay function)))
        all_events = types.InlineKeyboardMarkup()
        for i in sql.execute(f"SELECT * FROM events"):
            events_name = i[2]
            events_ids = i[0]
            events_com = i[4]
            print(f'{events_com}, {events_ids},{events_name}')
            print(events_ids)
            some_event = types.InlineKeyboardButton(events_name, callback_data=f'info_{events_ids}')
            all_events.insert(some_event)
        await message.answer(f"ивенты:", reply_markup=all_events)



if __name__ == '__main__':
    executor.start_polling(dp)
