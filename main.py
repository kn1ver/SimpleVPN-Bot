import asyncio
import aiogram

from config import BOT_TOKEN
from utils.logger import logger
from app.handlers import router_main

bot = aiogram.Bot(token=BOT_TOKEN)
disp = aiogram.Dispatcher()

async def main():
    try:
        disp.include_router(router_main)
        await disp.start_polling(bot, polling_timeout=60)
    except Exception as e:
        logger.critical(e)

if __name__ == '__main__':
    while True:
        try:
            logger.info("Бот запущен")
            asyncio.run(main())
        except Exception as e:
            logger.critical(e, exc_info=True)
            logger.info("Перезапускаю бота")
            continue
