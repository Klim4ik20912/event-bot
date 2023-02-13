import asyncio
import discord
import os
import config
import sqlite3
import database
import datetime
from datetime import timedelta
from discord.ext import commands
import typing
import random
import time
import json

intents = discord.Intents.default()
intents.members = True



bot = discord.Bot(intents=intents)
#date = datetime.now() + timedelta(days=7)
                    #datenow = date.strftime("%d-%m-%Y").format()
                    #sql.execute(f"UPDATE users SET end_premium = '{datenow}' WHERE user = {message.from_user.id}")
                    #await message.answer(f"{message.from_user.first_name}, ты успешно приобрел подписку PREMIUM 🔑", reply_markup=keyboard.menu)
                    #db.commit()

from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler()

db = sqlite3.connect("baza.db")
sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS users (
user INT,
username TEXT,
balance INT,
temp_stat DATETIME,
all_stat DATETIME,
warns INT
)""")
db.commit()

sql.execute("""CREATE TABLE IF NOT EXISTS shop (
role_id INT,
id INT,
cost BIGINT,
owner_id TEXT
)""")
db.commit()



@bot.event
async def on_member_join(member): # СОБЫТИЕ ЗАХОДА ПОЛЬЗОВАТЕЛЯ НА СЕРВЕР
    role = discord.utils.get(member.guild.roles, name='member 🌑') # САМА РОЛЬ КОТОРУЮ ВЫДАЕМ
    await member.add_roles(role) # ДОБАВЛЯЕМ РОЛЬ


@bot.event
async def on_voice_state_update(member, before, after):
    user = member.id
    if before.channel is None and after.channel is not None:
        print(f'{user} joined')
        con_time = datetime.datetime.now()
        database.voice_stat(user, con_time.strftime('%Y-%m-%d %H:%M:%S'))

    if after.channel is None and before.channel is not None:
        print(f'{user} left')
        time_now = datetime.datetime.now()
        n_t_now = time_now.strftime('%Y-%m-%d %H:%M:%S')
        temp_stat = sql.execute(f"SELECT temp_stat FROM users WHERE user = {user}").fetchone()[0]
        nn_t_now = datetime.datetime.strptime(n_t_now, '%Y-%m-%d %H:%M:%S')
        n_temp_stat = datetime.datetime.strptime(temp_stat, '%Y-%m-%d %H:%M:%S')
        disconnect_time = nn_t_now - n_temp_stat
        print(disconnect_time)
        database.voice_stat(user, disconnect_time)
        all_stat = sql.execute(f"SELECT all_stat FROM users WHERE user = {user}").fetchone()[0]
        print(all_stat)
        if all_stat != 0:
            if ' ' in all_stat:
                n_all_stat = datetime.datetime.strptime(all_stat, '%Y-%m-%d %H:%M:%S')
            else:
                n_all_stat = datetime.datetime.strptime(all_stat, '%H:%M:%S')
            sql.execute(f"UPDATE users SET all_stat = '{disconnect_time + n_all_stat}' WHERE user = {user}")
            db.commit()
        else:
            await member.send(f'🌄 Statistic Bot - {member.name}, добро пожаловать на lui 🕶 \nтеперь время проведенное в голосовых каналах будет включаться в статистику 👾')
            sql.execute(f"UPDATE users SET all_stat = '{disconnect_time}' WHERE user = {user}")
            db.commit()



@bot.slash_command(name = "stat", description = "Get stat From User_id")
async def hello(ctx, user: discord.Member):
    l = sql.execute(f"SELECT all_stat FROM users WHERE user = {user.id}").fetchone()[0]
    if ' ' in l:
        t = str(l).split(' ')[1]
        print('cjhccc')
    else:
        t = str(l)
    h = f'{str(t).split(".")[0].split(":")[0]} hours'
    mins = f'{str(t).split(".")[0].split(":")[1]} minutes'
    secs = f'{str(t).split(".")[0].split(":")[2]} seconds.'
    embed = discord.Embed(title=f"{user.display_name} - voice stat",
                          description=f"```{h}``` ```{mins}``` ```{secs}```")
    embed.set_thumbnail(url=str(user.display_avatar.url))
    await ctx.respond(embed=embed)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.playing, name="кумар 😮‍💨"))


@bot.slash_command(aliases=['add-shop'])
async def __add_shop(ctx, role: discord.Role = None, cost: int = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете внести в магазин")
    else:
        if cost is None:
            await ctx.send(f"**{ctx.author}**, укажите стоимость для данной роли")
        elif cost < 0:
            await ctx.send(f"**{ctx.author}**, стоимость роли не может быть такой маленькой")
        else:
            db.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
            db.commit()

            await ctx.message.add_reaction('✅')


@bot.slash_command(name = "getid", description = "Get Name From User_id")
async def hello(ctx, user: discord.Member):
    await ctx.respond(f"ID: {user.id}")

@bot.slash_command(name = "mute", description = "mute user")
@commands.has_role("🈂️Help 🈂️ x  Moderator 🛡️")
async def mute(ctx, user: discord.Member, time: int, reason):
    emb = discord.Embed(title=f"was muted! on {time}sec with reason - {reason}", colour=discord.Color.blue())
    await ctx.channel.purge(limit=1)

    emb.set_author(name=user.name, icon_url=user.avatar.url)
    emb.set_footer(text="mod - {}".format(ctx.author.name), icon_url=ctx.author.avatar.url)

    await ctx.send(embed=emb)
    await user.send(embed=emb)
    muted_role = discord.utils.get(user.guild.roles, name="muted")
    await user.add_roles(muted_role)
    await user.move_to(None)

    # Спим X секунд, перед тем как снять роль.
    await asyncio.sleep(time)
    # Снимаем роль замученного.
    await user.remove_roles(muted_role)


#create private rooms
# @bot.event
# async def on_voice_state_update(member, before, after):
#     if after.channel != None:
#         if after.channel.id == 1072873963727884328:
#             print('ABOBABABABA')
#             category = after.channel.category
#
#             channel2 = await member.guild.create_voice_channel(
#                 name=f'• {member.display_name} room 🌄',
#                 category=category
#             )
#
#             await channel2.set_permissions(member, connect=False)
#             await member.move_to(channel2)
#
#             def check(x, y, z): return len(channel2.members) == 0
#
#             await bot.wait_for('voice_state_update', check=check)
#             await channel2.delete()

@bot.slash_command(name = "coinflip", description = "Coinflip Game", pass_context=True)
async def coin(ctx, amount, bet_type):
    balance = database.balance(ctx.author.id)
    print(balance)
    print(ctx.author.id)
    print(bet_type)
    print(amount)
    if int(amount) > int(balance):
        await ctx.respond(f'Недостаточно средств для ставки!\n твой баланс - {balance}')
    else:
        numbs = [1, 2]
        r_numbs = random.choice(numbs)

        if r_numbs == 1 and bet_type == 'орел':
            db.execute(f"UPDATE users SET balance = balance + {amount} WHERE user = {ctx.author.id}")
            db.commit()
            await ctx.respond(f'ты выиграл! https://tenor.com/bRgdi.gif')
        elif r_numbs == 2 and bet_type == 'орел':
            db.execute(f"UPDATE users SET balance = balance - {amount} WHERE user = {ctx.author.id}")
            db.commit()
            await ctx.respond(f'ты проиграл! https://tenor.com/bRgdi.gif')
        if r_numbs == 2 and bet_type == 'решка':
            db.execute(f"UPDATE users SET balance = balance + {amount} WHERE user = {ctx.author.id}")
            db.commit()
            await ctx.respond(f'ты выиграл! https://tenor.com/bRgdi.gif')
        elif r_numbs == 1 and bet_type == 'решка':
            db.execute(f"UPDATE users SET balance = balance - {amount} WHERE user = {ctx.author.id}")
            db.commit()
            await ctx.respond(f'ты проиграл! https://tenor.com/bRgdi.gif')

@bot.slash_command(name="pay", description="Перевод суммы другому участнику")
async def pay(ctx, target: discord.Member, amount: int):
    balance = database.balance(ctx.author.id)
    if balance < amount:
        await ctx.send("У вас недостаточно средств для перевода")
        return

    # Снимаем сумму с аккаунта текущего пользователя
    db.execute(f"UPDATE users SET balance = balance - {amount} WHERE user = {ctx.author.id}")
    db.commit()

    # Начисляем указанную сумму на аккаунт другого пользователя
    db.execute(f"UPDATE users SET balance = balance + {amount} WHERE user = {target.id}")
    db.commit()

    await ctx.respond(f'✅ success transher to {target.display_name} in {amount} \n by {ctx.author.display_name}')



@bot.slash_command(name = "givemod", description = "Moderator Give Role")
@commands.has_role("dev 🈳️")
async def givemod(ctx, user: discord.Member):
    mod = discord.utils.get(user.guild.roles, name='🈂️Help 🈂️ x  Moderator 🛡️')  # САМА РОЛЬ КОТОРУЮ ВЫДАЕМ
    await user.add_roles(mod)  # ДОБАВЛЯЕМ РОЛЬ
    embed = discord.Embed(title=f"{user.display_name} - Mod",
                          description=f"```вам были выданы права модератора!```")
    embed.set_thumbnail(url=str(user.display_avatar.url))
    # await ctx.respond(f'```{user.mention}, ur balance - {balance} {format(user.avatar.url)}```')
    await user.send(embed=embed)


@bot.slash_command(name = "verify", description = "Verification User")
async def hello(ctx, user: discord.Member, sex):
    role = discord.utils.get(user.guild.roles, name='©access®')  # САМА РОЛЬ КОТОРУЮ ВЫДАЕМ
    del_role = discord.utils.get(user.guild.roles, name='member 🌑')  # САМА РОЛЬ КОТОРУЮ ОТНИМАЕМ
    fem_role = discord.utils.get(user.guild.roles, name='♀️')  # РОЛЬ ДЕВОЧКИ
    man_role = discord.utils.get(user.guild.roles, name='♂️')  # РОЛЬ МАЛЬЧИКА
    await user.add_roles(role)  # ДОБАВЛЯЕМ РОЛЬ
    await user.remove_roles(del_role)
    if sex == 'man':
        await user.add_roles(man_role)  # ДОБАВЛЯЕМ РОЛЬ
    elif sex == 'fem':
        await user.add_roles(fem_role)  # ДОБАВЛЯЕМ РОЛЬ
    sql.execute(f"INSERT INTO users VALUES (?,?,?,?,?,?)", (user.id, user.name, 0, 0, 0, 0))
    db.commit()
    await ctx.respond(f"✅ {user.name} успешно авторизован на сервере!")

@bot.slash_command(name = "balance", description = "User Balance")
async def balance(ctx, user: discord.Member):
    balance = database.balance(user.id)
    embed = discord.Embed(title=f"{user.display_name} - Balance", description=f"> **монетки {bot.get_emoji(1072647006037749790)}: **\n\n```{balance}    ```")
    embed.set_thumbnail(url=str(user.display_avatar.url))
    #await ctx.respond(f'```{user.mention}, ur balance - {balance} {format(user.avatar.url)}```')
    await ctx.respond(embed=embed)

@bot.slash_command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


@bot.slash_command()
async def huy(ctx):
    embed = discord.Embed(
        title="My Amazing Embed",
        description="Embeds are super easy, barely an inconvenience.",
        color=discord.Colour.blurple(),  # Pycord provides a class with default colors you can choose from
    )
    embed.add_field(name="A Normal Field",
                    value="A really nice field with some information. **The description as well as the fields support markdown!**")

    embed.add_field(name="Inline Field 1", value="Inline Field 1", inline=True)
    embed.add_field(name="Inline Field 2", value="Inline Field 2", inline=True)
    embed.add_field(name="Inline Field 3", value="Inline Field 3", inline=True)

    embed.set_footer(text="Footer! No markdown here.")  # footers can have icons too
    embed.set_author(name="Pycord Team", icon_url="https://example.com/link-to-my-image.png")
    embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
    embed.set_image(url="https://example.com/link-to-my-banner.png")

    await ctx.respond("Hello! Here's a cool embed.", embed=embed)  # Send the embed with some text

if __name__ == '__main__':
    # Запускаем бота
    bot.run(config.TOKEN)
