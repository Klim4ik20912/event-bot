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
from aiogram.utils.\
    helper import Helper, HelperMode, ListItem
from cgitb import text
import logging, sqlite3, aiogram, datetime, asyncio, random, keyboard
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import requests
from main import auth, get_timetable, get_userinfo, get_avatar
from datetime import timedelta
import json
from pyqiwip2p import QiwiP2P
from pyqiwip2p.p2p_types import QiwiCustomer, QiwiDatetime
import os


QIWI_ACCESS_KEY = '48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPtQ1o3oyVc8akMau8jrtLFz3d4UJHASSnTkGqAYrYmQWoyE7BsX2aYkU5T8B1HKeSBCDRVeQyfT8BqNbRo3eg3ecoadH3xPuAv8bbDvfbH'
p2p = QiwiP2P(auth_key=QIWI_ACCESS_KEY)

QIWI_TOKEN = '8de36906c8efef4c43a18425872a4710'
QIWI_NUMBER = '+79284642281'

db = sqlite3.connect("baza.db")
sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS users (
user INT,
user_group TEXT,
is_premium BOOL,
start_premium TEXT,
end_premium TEXT,
is_login INT,
login TEXT,
password TEXT,
access_token TEXT,
payment_code INT,
ava TEXT
)""")
db.commit()

bot = Bot(token='5731757099:AAHvDGHLqnx726-NpJGzR_dCcO3c0hmVtmM')

dp = Dispatcher(bot, storage=MemoryStorage())

cb = CallbackData("id", "text")

scheduler = AsyncIOScheduler()


class GetLogin(StatesGroup):
    login = State()
    password = State()


class Pop(StatesGroup):
    summa = State()


@dp.message_handler(state=Pop.summa)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        summa = 39
        lifetime = 15
        comment = sql.execute(f"SELECT payment_code FROM users WHERE user = {message.from_user.id}").fetchone()[0]
        await message.answer(f'⭐️ Стоимость Premium подписки: {summa}₽\nОбязательный комментарий: `{comment}`\n[Ссылка для оплаты](https://oplata.qiwi.com/create?publicKey={QIWI_ACCESS_KEY}&amount={summa}&comment={comment})',reply_markup=keyboard.pay, parse_mode='Markdown')
        await state.finish()


@dp.message_handler(Command("start"), state=None)
async def welcome(message):
    if message.from_user.id == message.chat.id:
        sql.execute(f"SELECT * FROM users WHERE user = {message.from_user.id}")
        if sql.fetchone() is None:
            sql.execute(f"INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)", (message.from_user.id, 'None', False, None, None, 0, 'NULL', 'NULL', 'NULL', 0, 'NULL'))
            db.commit()
            await message.answer(f"{message.from_user.first_name}, я тебя зарегистрировал", reply_markup=keyboard.start,
                                 parse_mode='Markdown')
        else:
            await message.answer(f"приветствую, {message.from_user.first_name}, я 晚餐 бот", reply_markup=keyboard.menu,
                                 parse_mode='Markdown')
    elif message.from_user.id != message.chat.id:
        sql.execute(f"SELECT * FROM users WHERE user = {message.from_user.id}")
        if sql.fetchone() is None:
            await message.reply("похоже что ты не зарегестрирован\nнапиши /start в личные сообщения боту")
        else:
            await message.answer(f"привет, {message.from_user.first_name}, я 晚餐", parse_mode='Markdown',
                                 reply_markup=keyboard.menu)


@dp.message_handler(state=GetLogin.password)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        password = message.text
        await state.finish()
        sql.execute(f"UPDATE users SET password = '{password}' WHERE user = {message.from_user.id}")
        db.commit()
        try:
            login = sql.execute(f"SELECT login FROM users WHERE user = {message.from_user.id}").fetchone()[0]
            password = sql.execute(f"SELECT password FROM users WHERE user = {message.from_user.id}").fetchone()[0]
            res = auth(login, password)
            if res != None:
                await message.answer('✅ Ты успешно авторизован в боте', reply_markup=keyboard.menu)
                sql.execute(f"UPDATE users SET access_token = '{res}' WHERE user = {message.from_user.id}")
                sql.execute(f"UPDATE users SET is_login = {1} WHERE user = {message.from_user.id}")
                db.commit()
                print(f'{res} sssss')
            else:
                await message.answer('❌ что-то пошло не так, попробуй авторизоваться еще раз',
                                     reply_markup=keyboard.start)
        except:
            await message.answer('㊙️ что-то пошло не так попробуй еще раз :)', reply_markup=keyboard.start)
            print('error suka')


@dp.message_handler(state=GetLogin.login)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        login = message.text
        await state.finish()
        sql.execute(f"UPDATE users SET login = '{login}' WHERE user = {message.from_user.id}")
        db.commit()
        await message.answer(f"введи пароль от журнала:")
        await GetLogin.password.set()


def is_login(user_id):
    is_login = sql.execute(f"SELECT is_login FROM users WHERE user = {user_id}").fetchone()[0]
    if is_login == 0:
        return '👾 вы не авторизованы.'
    elif is_login == 1:
        return True

def check_premium(user_id):
    try:
        is_prem = sql.execute(f"SELECT is_premium FROM users WHERE user = {user_id}").fetchone()[0]
        if is_prem != 0:
            now = datetime.now()
            if now.strftime("%d-%m-%Y") > sql.execute(f"SELECT end_premium FROM users WHERE user = {user_id}").fetchone()[0]:
                sql.execute(f'UPDATE users SET is_premium = {0} WHERE user = {user_id}')
                db.commit()
                return 'Подписка Premium закончилась, приобрести новую можно: мой профиль→подписка'
            else:
                return True
        else:
            'у вас нету подписки Premium, приобрести можно: мой профиль→подписка'
    except:
        return '㊙️ error, maybe your subscribe is not available'



@dp.message_handler(content_types=['text'])
async def main(message: types.Message):
    if message.text == 'Premium подписка':
        random_code = random.randint(1000, 9999)
        sql.execute(f"UPDATE users SET payment_code = {random_code} WHERE user = {message.from_user.id}")
        db.commit()
        await Pop.summa.set()

    if message.text == 'проверить оплату':
        print('check')
        session = requests.Session()
        session.headers['authorization'] = 'Bearer ' + QIWI_TOKEN
        parameters = {'rows': '5'}
        h = session.get(
            'https://edge.qiwi.com/payment-history/v1/persons/{}/payments'.format(QIWI_NUMBER),
            params=parameters)
        req = json.loads(h.text)
        for i in sql.execute(f"SELECT payment_code FROM users WHERE user = {message.from_user.id}"):
            comment = str(i[0])
        for i in range(len(req['data'])):
            s1 = req["data"][i]["sum"]["amount"]
            if comment in str(req['data'][i]['comment']):
                if int(s1) >= 39:
                    sql.execute(f'UPDATE users SET is_premium = {1} WHERE user = {message.from_user.id}')
                    date = datetime.now() + timedelta(days=7)
                    datenow = date.strftime("%d-%m-%Y").format()
                    sql.execute(f"UPDATE users SET end_premium = '{datenow}' WHERE user = {message.from_user.id}")
                    await message.answer(f"{message.from_user.first_name}, ты успешно приобрел подписку PREMIUM 🔑", reply_markup=keyboard.menu)
                    db.commit()
                    #return 1, req["data"][i]["sum"]["amount"]
                else:
                    await message.answer('сумма меньше 39р, обртатитесь @xxlv.young для доплаты или возврата денег')
        else:
                await message.answer(f"Я не нашёл оплату\nЕсли произошла ошибка - обратись @xxlv_young", reply_markup=keyboard.menu)
                return 0, 0

    if message.text == 'войти в журнал':
        if sql.execute(f"SELECT is_login FROM users WHERE user = {message.from_user.id}").fetchone()[0] == 1:
            await message.answer('ты уже авторизован в боте!', reply_markup=keyboard.menu)
        else:
            await message.answer('напиши логин от журнала:')
            await GetLogin.login.set()
    if message.text == 'расписание 📚':
        try:
                is_l = is_login(message.from_user.id)
                if is_l == True:
                    #is_premium = sql.execute(f"SELECT is_premium FROM users WHERE user = {message.from_user.id}").fetchone()[0]
                    #if is_premium == 0:
                        #await message.answer('эта функция доступна только по подписке Premium. мой профиль→подписка')
                        token = sql.execute(f"SELECT access_token FROM users WHERE user = {message.from_user.id}").fetchone()[0]
                        date = datetime.now()
                        if date.hour <= 16:
                            datenow = date.strftime("%Y-%m-%d")
                            a = get_timetable(token, datenow)
                            b = len(a)
                            if b == 0:
                                await message.answer(f'расписание еще не составили или в этот день нет пар',
                                                     reply_markup=keyboard.menu)
                            elif b == 1:
                                await message.answer(f'🌇 {a[0]}')
                            elif b == 2:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]}')
                            elif b == 3:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]}')
                            elif b == 4:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]} \n 🌆 {a[3]}')
                            elif b == 5:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]} \n 🌆 {a[3]} \n 🌃 {a[4]}')
                            else:
                                await message.answer(
                                    '㊙️ ошибка, что-то пошло не так, попробуйте пересоздать токен в настройках',
                                    reply_markup=keyboard.menu)
                        else:
                            date = datetime.now() + timedelta(hours=10)
                            datenow = date.strftime("%Y-%m-%d")
                            print(datenow)
                            a = get_timetable(token, datenow)
                            b = len(a)
                            if b == 0:
                                await message.answer(f'расписание еще не составили или в этот день нет пар',
                                                     reply_markup=keyboard.menu)
                            elif b == 1:
                                await message.answer(f'🌇 {a[0]}')
                            elif b == 2:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]}')
                            elif b == 3:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]}')
                            elif b == 4:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]} \n 🌆 {a[3]}')
                            elif b == 5:
                                await message.answer(f'🌇 {a[0]} \n 🏙 {a[1]} \n 🏙 {a[2]} \n 🌆 {a[3]} \n 🌃 {a[4]}')
                            else:
                                await message.answer(
                                    '㊙️ ошибка, что-то пошло не так, попробуйте пересоздать токен в настройках',
                                    reply_markup=keyboard.menu)
                else:
                    await message.answer(is_l, reply_markup=keyboard.start)

        except:
            await message.answer('㊙️ ошибка, возможно ваша подписка недействительна')


    if message.text == 'user_info':
        is_l = is_login(message.from_user.id)
        if is_l == True:
            token = sql.execute(f"SELECT access_token FROM users WHERE user = {message.from_user.id}").fetchone()[0]
            b = get_userinfo(token)
            await message.answer(f'profile {b}')
        else:
            await message.answer(is_l, reply_markup=keyboard.start)

    if message.text == 'деавторизация':
        sql.execute(f"UPDATE users SET is_login = {0} WHERE user = {message.from_user.id}")
        sql.execute(f"UPDATE users SET login = 'NULL' WHERE user = {message.from_user.id}")
        sql.execute(f"UPDATE users SET password = 'NULL' WHERE user = {message.from_user.id}")
        db.commit()
        await message.answer('вы успешно деавторизованы', reply_markup=keyboard.start)
    if message.text == 'обновить токен 🔄':
        try:
            login = sql.execute(f"SELECT login FROM users WHERE user = {message.from_user.id}").fetchone()[0]
            password = sql.execute(f"SELECT password FROM users WHERE user = {message.from_user.id}").fetchone()[0]
            res = auth(login, password)
            await message.answer('token was successfully updated!')
            sql.execute(f"UPDATE users SET access_token = '{res}' WHERE user = {message.from_user.id}")
            db.commit()
        except:
            await message.answer('㊙️ что-то пошло не так, возможно данные для входа неверны',
                                 reply_markup=keyboard.menu)

    if message.text == 'мой профиль 👔':
        try:
            is_l = is_login(message.from_user.id)
            if is_l == True:
                token = sql.execute(f"SELECT access_token FROM users WHERE user = {message.from_user.id}").fetchone()[0]
                res = get_userinfo(token)
                avatar = get_avatar(token, message.from_user.id)
                print(avatar)
                #for i in os.walk('avatars'):
                    #if i == f'ava_{message.from_user.id}':
                        #ava = i
                # await message.answer(f'{res}', reply_markup=keyboard.my_profile)
                await bot.send_photo(message.from_user.id, types.InputFile(f'avatars/ava_{message.from_user.id}.jpg'), caption=res, reply_markup=keyboard.my_profile)
                #await message.answer(res, reply_markup=keyboard.my_profile)
            else:
                await message.answer(is_l, reply_markup=keyboard.start)
        except:
            await message.answer('㊙️ ошибка, что-то пошло не так, попробуйте обновить токен в настройках')

    if message.text == 'назад в меню':
        await message.answer('главное меню', reply_markup=keyboard.menu)

    if message.text == 'настройки ⚙️':
        is_l = is_login(message.from_user.id)
        if is_l == True:
            await message.answer('⚙️ (v0.8)', reply_markup=keyboard.settings)
        else:
            await message.answer(is_l, reply_markup=keyboard.start)

    if message.text.startswith('pm_'):
        message_text = message.text
        pm_text = message_text[message_text.find("_") + 1:]
        for i in sql.execute("SELECT user FROM users"):
            await bot.send_message(i[0], text=pm_text)


async def notifs():
    print('notifs')
    try:
        date = datetime.now()
        weekend = date.isoweekday()
        print(weekend)
        if weekend != 6 and weekend != 7:
            if date.hour == 8 and date.minute == 50:
                a = '🌇 скоро начало первой пары.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 9 and date.minute == 45:
                a = '🔔 5 минутный перерыв.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 10 and date.minute == 35:
                a = '🔫 конец первой пары, 10-минутный перерыв 🚬'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 11 and date.minute == 30:
                a = '👾 5 минут перерыв.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 12 and date.minute == 20:
                a = '🍻 50 минут перерыв на обед)'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 12 and date.minute == 59:
                a = '😥 начинается 3 пара.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 13 and date.minute == 45:
                a = '😴 перерыв 5 минут.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 14 and date.minute == 35:
                a = '😎 3 пара подошла к концу, у тебя 10 минут.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 14 and date.minute == 45:
                a = '😡 последняя пара.'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 15 and date.minute == 30:
                a = '👽 перерыв?'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            if date.hour == 16 and date.minute == 20:
                a = '🤓 домой!!!'
                for i in sql.execute("SELECT user FROM users"):
                    await bot.send_message(i[0], text=a)
            else:
                pass

            #if date.hour == 13 and date.minute == 47:
                #a = '🤓 домой!!!'
                #for i in sql.execute("SELECT user FROM users"):
                    #await bot.send_message(i[0], text=a)
    except:
        print('some error 401')



async def on_startup(dp):
    # Каждые 60 минут запускаем рассылку
    scheduler.add_job(notifs, "interval", seconds=45)
    print('')
    print('-------------------------------')
    print('  Скрипт запущен.')
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
