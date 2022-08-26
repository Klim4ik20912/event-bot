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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from geopy.geocoders import Nominatim
import ssl
import certifi
import geopy.geocoders

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx

# calling the nominatim tool
geoLoc = Nominatim(user_agent="GetLoc")
scheduler = AsyncIOScheduler()

random_notif = [
    'совсем скоро 💤\n одевайся 🌌', 'уже на носу 🚀 \n встанешь с кровати?', 'на быстром старте. \n все ждут тебя 🏝', 'тик-так 🌆 \n скоро начинаем)', 'уже открывают пиво 🍺. \n советую поторопиться',
    'гадают где же ты 🔮 \n ну серьезно, ты скоро?', 'уже включили музыку 🔊 \n успей подключится к колонке'
]

random_greeting = [
    'хей', 'привет', 'здаров', 'как жизнь', 'ку',
]


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

bot = Bot(token='YOUR BOT TOKEN')

dp = Dispatcher(bot, storage=MemoryStorage())

cb = CallbackData("id", "text")


class CreateEvent(StatesGroup):
    event = State()
    time = State()
    place = State()
    comment = State()

class GetPlace(StatesGroup):
    get = State()
    geocode = State()





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
        await message.answer("Напиши число ивента (например: 2022.07.09.14.30")
        await CreateEvent.time.set()

@dp.message_handler(state=CreateEvent.time)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        global e_time
        e_time = message.text
        await state.finish()
        await message.answer("отправь геолокацию где будет проходить тусовка.", parse_mode='Markdown')
        await CreateEvent.place.set()

@dp.message_handler(content_types=['location'], state=CreateEvent.place)
async def process_name(message: types.location, state: FSMContext):
    async with state.proxy() as data:
        global e_place
        lat = message['location']['latitude']
        long = message['location']['longitude']
        e_place = f'{lat}, {long}'
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

@dp.message_handler(state=GetPlace.get, content_types=['location'])
async def main(message : types.Location, state: FSMContext):
    async with state.proxy() as data:
        lat = message['location']['latitude']
        long = message['location']['longitude']
        locname = geoLoc.reverse(f'{lat}, {long}')
        print(locname)
        event_id = sql.execute(f'SELECT events FROM users WHERE user = {message.from_user.id}').fetchone()[0]
        print(f'event id {event_id}')
        event_place = sql.execute(f'SELECT place FROM events WHERE id = {event_id}').fetchone()[0]
        event_geocode = geoLoc.reverse(event_place)
        await state.finish()
        if str(locname) in event_geocode:
            await bot.send_message(message.from_user.id, 'удачно повеселиться :)', reply_markup=keyboard.events_func)
        else:
            await bot.send_message(message.from_user.id, 'не ври алгоритму :( \n мне обидно...', reply_markup=keyboard.start)

@dp.callback_query_handler(lambda c: c.data and c.data =='inplace')
async def statistics(message: types.Message):
    await message.answer('отправь свою геолокацию для проверки.')
    await GetPlace.get.set()

def people_counter(event_id):
    peoples = sql.execute(f"SELECT user FROM users WHERE events = {event_id}").fetchall()
    return peoples

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('info_'))
async def check(call: types.CallbackQuery):
        event_id = call.data[call.data.find("_") + 1 : ]
        print(event_id)
        for info in sql.execute(f"SELECT * FROM events WHERE id = {event_id}"):
                notgo = types.InlineKeyboardMarkup()
                inotgo = types.InlineKeyboardButton('я не иду', callback_data=f'notgo_{info[0]}')
                isgo = types.InlineKeyboardMarkup()
                igo = types.InlineKeyboardButton('я пойду', callback_data=f'isgo_{info[0]}')
                ionplace = types.InlineKeyboardMarkup()
                inplace = types.InlineKeyboardButton(text='на месте 📍', callback_data='inplace', request_location=True)
                isgo.add(igo, inotgo).add(inplace)
                peoples = people_counter(event_id)
                print(f'человек {peoples}')
                if peoples == None:
                    peoples = 0
                desc_event = f'🎸 тусовка - {info[2]} \n⌚ {info[3]}  \n📍 place: {info[5]} \n✉ комментарий: {info[4]} \n🕶 идет: {len(peoples)} человек \n (id: {info[0]})'
                await call.message.answer(desc_event, reply_markup=isgo)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('isgo_'))
async def check(call: types.CallbackQuery):
    event_id = call.data[call.data.find("_") + 1:]
    sql.execute(f"UPDATE users SET events = {event_id} WHERE user = {call.from_user.id} ")
    db.commit()
    await call.message.answer('записал тебя в базу данных :)', reply_markup=keyboard.start)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('notgo_'))
async def check(call: types.CallbackQuery):
    event_id = call.data[call.data.find("_") + 1:]
    event_state = sql.execute(f"SELECT events FROM users WHERE user = {call.from_user.id}").fetchone()[0]
    if event_state != 'None':
        sql.execute(f"UPDATE users SET events = 'None' WHERE user = {call.from_user.id} ")
        db.commit()
        await call.message.answer('жаль что ты не пойдешь(', reply_markup=keyboard.start)
    else:
        await call.message.answer('ты и не собирался)', reply_markup=keyboard.start)

@dp.message_handler(content_types=['text'])
async def main(message : types.Message):
    if message.text == 'ивенты':
        for i in sql.execute(f"SELECT events FROM users WHERE user = {message.from_user.id}"):
            some_events = i
            print(some_events[0])
            if some_events[0] != 'None':
                for i in sql.execute(f"SELECT name, id FROM events WHERE id = {some_events[0]}"):
                    event_name = i[0]
                    event_id = i[1]
                    event_but = types.InlineKeyboardMarkup()
                    some_event = types.InlineKeyboardButton(event_name, callback_data=f'info_{event_id}')
                    event_but.insert(some_event)
                    rand_greet = random.choice(random_greeting)
                    await message.answer(f'{rand_greet}, {message.from_user.first_name}. твои тусовки:', reply_markup=event_but, parse_mode='Markdown')
                    await message.answer(f"меню", reply_markup=keyboard.events_func, parse_mode='Markdown')
            else:
                await message.answer(f"привет, {message.from_user.first_name}, у тебя нету активных ивентов", reply_markup=keyboard.events_func, parse_mode='Markdown')
    if message.text == 'settings':
        await message.answer(f"{message.from_user.first_name}, настройки (v1.8)", reply_markup=keyboard.settings, parse_mode='Markdown')
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
        b = sql.execute(f"SELECT * FROM events").fetchall()
        print(b)
        if b != []:
            await message.answer(f"доступные тусовки:", reply_markup=all_events)
        else:
            await message.answer(f"на данный момент нету активных тусовок. \n попробуй заглянуть позже 🏜", reply_markup=all_events)

    if message.text == 'quit patry':
        sql.execute(f"UPDATE users SET events = 'None' WHERE user = {message.from_user.id}")
        db.commit()
        await message.answer(f"отписал тебя от ивента.", reply_markup=keyboard.start)

    if message.text.startswith('rm_'):
        e_event = message.text
        del_event = e_event[e_event.find("_") + 1:]
        sql.execute(f"DELETE FROM events WHERE id={del_event}")
        db.commit()
        await message.answer(f'ивент {del_event} был удален из базы.')

    if message.text == 'на месте 📍':
        await message.answer('пришли свою геолокацию для проверки')
        await GetPlace.get.set()


async def notification():
    print('notification')
    for i in sql.execute(f"SELECT * FROM events"):
        time = i[3]
        event_id = i[0]
        event_name = i[2]
        now = datetime.datetime.now()
        date_time_str = now.strftime("%Y.%m.%d.%H.%M")
        events_time = datetime.datetime.strptime(time, '%Y.%m.%d.%H.%M')
        count = events_time - now
        if int(count.seconds / 3600) <= 1 and int(count.seconds / 3600) > -1:
            print('yessss')
            for b in sql.execute(f"SELECT user FROM users WHERE events = {event_id}"):
                some_notif = random.choice(random_notif)
                caption = f'📢 ивент - {event_name}. \n {some_notif}'
                await bot.send_message(b[0], str(caption))
        else:
            print('нет доступных уведомлений :(')



async def on_startup(dp):
    # Каждые 60 минут запускаем рассылку
    scheduler.add_job(notification, "interval", minutes=60)
    print('')
    print('-------------------------------')
    print('  Скрипт бота тг для бани запущен.')
    print('  Разработчик: Клим Черемных ')
    print('  GitHub: https://github.com/Klim4ik20912')
    print('  Вк: https://vk.com/kl_life')
    print('  Дс: oper#7040')
    print('-------------------------------')
    print('')

    await bot.send_message(732652304, 'Бот запущен!')


if __name__ == '__main__':
    # Запускаем бота
    scheduler.start()
    executor.start_polling(dp, on_startup=on_startup)
