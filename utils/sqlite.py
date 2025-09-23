import aiosqlite
from utils.logger import logger

async def create_db() -> None:
    """
    Создает базу данных.
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute('CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, activate_key TEXT, activated INTEGER, aes_key TEXT, paid INTEGER)')
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

async def set_paid(user_id: str, value: int | None=1):
    """
    Задает значение оплаты
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"UPDATE users SET paid = '{value}' WHERE chat_id = '{user_id}'")
        await connection.commit()

    logger.debug(f"Для пользователя {user_id} оплата установлена на {value}")
    return True

async def set_aes_key(user_id: str, key: str):
    """
    Устанавливает ключ шифровки/дешифровки конфига пользователя
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"UPDATE users SET aes_key = '{key}', activated = '0' WHERE chat_id = '{user_id}'")
        await connection.commit()

    logger.debug(f"Для пользователя {user_id} aes_key установлен на {key}")
    return True

async def set_activate_key(user_id: str, key: str):
    """
    Устанавливает ключ активации пользователя
    """

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"UPDATE users SET activate_key = '{key}', activated = '0' WHERE chat_id = '{user_id}'")
        await connection.commit()

    logger.debug(f"Для пользователя {user_id} activate_key установлен на {key}")
    return True

async def get_user_data(user_id: str, columns: list) -> list:
    """
    Возвращает список со значениями запрошенных столбцов.
    """

    parsed_columns = ', '.join(columns)

    async with aiosqlite.connect('bot.sql') as connection:
        cursor = await connection.cursor()
        await cursor.execute(f"SELECT {parsed_columns} FROM users WHERE chat_id = '{user_id}'")
        user_data = await cursor.fetchall()

    logger.debug(f"user_data ({parsed_columns}): {user_data[0]}")
    return user_data[0]
