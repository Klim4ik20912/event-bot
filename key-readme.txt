from aiogram import Bot, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start = types.ReplyKeyboardMarkup(resize_keyboard=True)
settings = types.ReplyKeyboardMarkup(resize_keyboard=True)
my_profile = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
pay = types.ReplyKeyboardMarkup(resize_keyboard=True)


login_but = types.KeyboardButton("войти в журнал")
refresh_but = types.KeyboardButton("обновить токен 🔄")

back_menu = types.KeyboardButton("назад в меню")


timetable = types.KeyboardButton("расписание 📚")
settings_but = types.KeyboardButton("настройки ⚙️")
profile = types.KeyboardButton("мой профиль 👔")

subscribe = types.KeyboardButton("Premium подписка")
deauth_but = types.KeyboardButton("деавторизация")

pay_but = types.KeyboardButton("проверить оплату", callback_data='check')

pay.add(pay_but)

settings.add(refresh_but, deauth_but).add(back_menu)
my_profile.add(subscribe, back_menu)
start.add(login_but)
menu.add(timetable, profile).add(settings_but)
