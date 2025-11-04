import asyncio
import aiogram
from config import BOT_TOKEN
from utils.logger import logger
from utils.timeToPay import *
from app.handlers import router_main


async def notify_service(bot: aiogram.Bot):
    """Фоновая задача проверки оплат"""
    while True:
        try:
            await set_paid_0()
            chat_ids = await db_search()
            for (chat_id,) in chat_ids:
                await notify_user(str(chat_id), bot)
        except Exception as e:
            logger.error(f"Ошибка в notify_service: {e}", exc_info=True)
        await asyncio.sleep(3600 * 24)


async def start_bot():
    """Один цикл жизни бота"""
    bot = aiogram.Bot(token=BOT_TOKEN)
    disp = aiogram.Dispatcher()
    disp.include_router(router_main)

    asyncio.create_task(notify_service(bot))

    try:
        await disp.start_polling(bot, polling_timeout=60)
    finally:
        await bot.session.close()


async def main():
    """Главный перезапускающий цикл"""
    while True:
        try:
            logger.info("Бот запущен")
            await start_bot()
        except Exception as e:
            logger.critical(f"Сбой в работе бота: {e}", exc_info=True)
            logger.info("Перезапускаю бота через 5 секунд…")
            await asyncio.sleep(5)
        else:
            # если polling завершился без исключения — выйти
            logger.info("Бот остановлен вручную.")
            break


if __name__ == "__main__":
    asyncio.run(main())
