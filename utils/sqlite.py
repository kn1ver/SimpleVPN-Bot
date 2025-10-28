import aiosqlite
from utils.logger import logger

async def create_db() -> None:
    """
    Создает базу данных.
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute('CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, activate_key TEXT, activated INTEGER, paid INTEGER)')
        await connection.commit()

    logger.debug("База данных создана")

    return True

async def reg_user(user_id: str):
    """
    Регистрирует пользователя в бд
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"INSERT INTO users (chat_id, paid) VALUES ({user_id}, 0)")
        await connection.commit()

    logger.debug(f"Пользователь {user_id} зарегистрирован")
    return True


async def set_user_data(filter: str, filter_value: str, key: str, value: str):
    """
    Задает key значние value по filter 
    """

    query = f"UPDATE users SET {key} = '{value}' WHERE {filter} = '{filter_value}'"

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(query)
        await connection.commit()


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

    return user_data[0]


async def search_for_key(key):
    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"SELECT activated FROM users WHERE activate_key = '{key}'")
        data = await cursor.fetchall()

    if data and data[0]:
        activated = data[0]
    else:
        return [True]

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"SELECT chat_id FROM users WHERE activate_key = '{key}'")
        data = await cursor.fetchall()

    return [chat_id, activated]

async def set_activated(user_id: str, value: int):
    """
    Устанавливает ключ активации пользователя
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"UPDATE users SET activated = '{value}' WHERE chat_id = '{user_id}'")
        await connection.commit()

    logger.debug(f"Для пользователя {user_id} activated установлен на {value}")
    return True
