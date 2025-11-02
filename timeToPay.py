# TODO служба отслеживания сроков до окончания подписки и предупреждения пользователей о конце оплаченного преиода
import aiosqlite
import asyncio
import time

from utils.logger import set_logger
from utils import utils
from config import BOT_TOKEN
from app import keyboards as markup

from aiogram import F, Router, Bot
from datetime import datetime, timedelta

logger = set_logger("logs/timeToPay.log", False)

async def db_search():
    now = int(time.time()) * 1000
    limit = now + int(timedelta(days=8).total_seconds() * 1000)
    
    query = "SELECT chat_id FROM users WHERE expires_at < ? AND expires_at > ?"
    params = (limit, now)

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(query, params)
        data = await cursor.fetchall()

    return data

async def get_user_data(filter: str, filter_value: str, columns: list) -> list:
    """
    Возвращает список со значениями запрошенных столбцов.
    """

    parsed_columns = ', '.join(columns)
    query = f"SELECT {parsed_columns} FROM users WHERE {filter} = '{filter_value}'"

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(query)
        user_data = await cursor.fetchall()

    return user_data

async def notify_user(chat_id: str, bot: Bot):

    user_data = await get_user_data("chat_id", chat_id, ["expires_at"])

    now = int(time.time()) * 1000
    expires_at = user_data[0][0]
    time_for_end = utils.time_parser((expires_at - now)/1000)

    await bot.send_message(
        chat_id=chat_id,
        text=f'❗️ До истечения подписки осталось: {time_for_end}\nВы можете продлить её с помощью кнопки снизу или в разделе "Оплатить VPN"',
        reply_markup=markup.pay_vpn
    )

async def set_paid_0():
    """
    Сбрасывает поле paid = 0 у всех пользователей,
    чья подписка истекла (expires_at < текущее время).
    """
    now = int(time.time()) * 1000
    query = "UPDATE users SET paid = 0 WHERE expires_at < ?"

    async with aiosqlite.connect("bot.sql") as connection:
        async with connection.execute(query, (now,)) as cursor:
            await connection.commit()
            updated_rows = cursor.rowcount  # сколько строк изменено

    return updated_rows

