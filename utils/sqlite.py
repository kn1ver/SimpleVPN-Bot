import aiosqlite
from utils.logger import logger

async def create_db() -> None:
    """
    Создает базу данных.
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute('CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, xui_id TEXT, activated INTEGER, paid INTEGER, bought_at INTEGER, expires_at INTEGER)')
        await connection.commit()

    return True

async def reg_user(user_id: str):
    """
    Регистрирует пользователя в бд
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"INSERT INTO users (chat_id, xui_id, activated, paid) VALUES (?, ?, ?, ?)", (user_id, None, 0, 0,))
        await connection.commit()

    logger.debug(f"Пользователь {user_id} зарегистрирован")
    return True


async def set_user_data(filter: str, filter_value: str, key: str, value):
    """
    Задает для key значение: value по filter 
    """

    query = f"UPDATE users SET {key} = '{value}' WHERE {filter} = '{filter_value}'"

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(query)
        await connection.commit()

    logger.debug(f"set_usr_data| Изменение данных пользователя\nФильтр: {filter} | Значение: {filter_value}\nПоле: {key} | Значение: {value}")


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

    logger.debug(f"sqlite | get_usr_data:\n{user_data}")
    return user_data


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
