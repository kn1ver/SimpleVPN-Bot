import asyncio
import aiogram

from config import BOT_TOKEN
from utils.logger import logger
from app.handlers import router_main

from timeToPay import *

bot = aiogram.Bot(token=BOT_TOKEN)
disp = aiogram.Dispatcher()

async def notify_service(bot: Bot):
    while True:
            chat_ids = await db_search()
            for (chat_id,) in chat_ids:
                await notify_user(str(chat_id), bot)
            await asyncio.sleep(3600*24)

async def main():
    try:
        # asyncio.create_task(notify_service(bot))
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
