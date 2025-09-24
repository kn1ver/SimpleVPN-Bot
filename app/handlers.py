import app.keyboards as markup
import os
import shutil
from pathlib import Path

from utils.logger import logger
from utils import xui
from utils import sqlite as db
from utils import utils as utils
from config import MESSAGES

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

router_main = Router()

@router_main.message(Command('start'))
async def start (message: Message, bot: Bot):
    try:
        await message.answer(text='Добро пожаловать. Что вас интересует?', reply_markup=markup.start)

        try:
            await db.create_db()
            await db.reg_user(message.chat.id)
        except:
            pass

        # await bot.send_message(
            # chat_id=1616183086,
            # text=f'Пользователь {message.from_user.full_name} | @{message.from_user.username} | {message.chat.id} открыл бота')
    except Exception as e:
        logger.error(e)

@router_main.callback_query(lambda c: "profile" in c.data)
async def profile(callback: CallbackQuery, bot: Bot):
    try:
        client = xui.get_user_data(str(callback.message.chat.id))
        logger.debug(client)

        if not client or not client["PC"]["enable"]:
            await callback.message.edit_text(
                text="Похоже, Вы еще не подключены к нашему VPN или не оплатили текущий период",
                reply_markup=markup.pay_vpn)

        msg_pc = (
            f"<b>   PC\n</b>"
            f"💡Активен: {'✅ Да' if client["PC"]['enable'] else '🔴 Нет'}\n"
            f"🌐 Статус соединения: {'🟢 Онлайн' if client["PC"]['online'] else '🔴 Офлайн'}\n"
            f"🔼 Загрузка: {client["PC"]["up"]}\n🔽 Скачивание: {client["PC"]["down"]}\n"
            f"📅 Окончание через: {client["PC"]["expiryTime"]}\n\n"
        ) if client["PC"] else ""

        msg_android = (
            f"<b>   Andoid\n</b>"
            f"💡Активен: {'✅ Да' if client["Android"]['enable'] else '🔴 Нет'}\n"
            f"🌐 Статус соединения: {'🟢 Онлайн' if client["Android"]['online'] else '🔴 Офлайн'}\n"
            f"🔼 Загрузка: {client["Android"]["up"]}\n🔽 Скачивание: {client["Android"]["down"]}\n"
            f"📅 Окончание через: {client["Android"]["expiryTime"]}\n\n"
        ) if client["Android"] else ""

        msg_ios = (
            f"<b>   IOS\n</b>"
            f"💡Активен: {'✅ Да' if client["IOS"]['enable'] else '🔴 Нет'}\n"
            f"🌐 Статус соединения: {'🟢 Онлайн' if client["IOS"]['online'] else '🔴 Офлайн'}\n"
            f"🔼 Загрузка: {client["IOS"]["up"]}\n🔽 Скачивание: {client["IOS"]["down"]}\n"
            f"📅 Окончание через: {client["IOS"]["expiryTime"]}\n\n"
        ) if client["IOS"] else ""

        msg = f"Ваши устройства:\n\n{msg_pc + msg_android + msg_ios}"

        await callback.message.edit_text(
            text=msg,
            reply_markup=markup.to_main,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(e, exc_info=True)

@router_main.callback_query(lambda c: "return" in c.data)
async def return_to(callback: CallbackQuery, bot: Bot):
    try:
        if "main" in callback.data:
            await callback.message.edit_text(text='Добро пожаловать. Что вас интересует?', reply_markup=markup.start)

        elif "platforms" in callback.data:
            await callback.message.edit_text(text='На какую платформу Вы хотите установить VPN?', reply_markup=markup.platforms)

    except Exception as e:
        logger.error(e)

@router_main.callback_query(lambda c: "install" in c.data)
async def install_vpn(callback: CallbackQuery, bot: Bot):

    chat_id = str(callback.message.chat.id)

    if "vpn" in callback.data:
        try:

            user_paid = await db.get_user_data(chat_id, ["paid"])

            if not user_paid[0]:
                await callback.message.edit_text(
                    text="Вы еще не приобрели доступ к VPN или оплата просрочена",
                    reply_markup=markup.pay_vpn
                )
                return

            await callback.message.edit_text(
                text="На какую платформу Вы хотите установить VPN?",
                reply_markup=markup.platforms)
        except Exception as e:
            logger.error(e)

    elif "pc" in callback.data:
        try:
            xui_data = xui.get_user_data(chat_id)
            access_key = xui_data["PC"]["id"]
            msg = "С порядоком установки VPN на компьютер вы можете ознакомиться по этой ссылке:\n" \
                    "https://teletype.in/@kn1ver/install-pc \n\n" \
                    f"Ваш ключ доступа: <code>{access_key}</code>\n\n Архивы отправляются ▯▯▯▯▯▯▯▯▯▯"

            msg_id = await callback.message.edit_text(
                text=msg,
                reply_markup=markup.to_platforms,
                parse_mode="HTML")

            archive, dll, dst, archive_path = await utils.get_archive(chat_id, bot, int(msg_id.message_id), access_key)
            launcher = FSInputFile("files/first_launch.exe")

            await callback.message.answer_document(launcher)
            await callback.message.answer_document(archive)
            msg = msg[:-10] + "▮▮▮▮▮▮▮▯▯▯"
            await callback.message.edit_text(text=msg, parse_mode="HTML")

            await callback.message.answer_document(dll)
            msg = msg[:-10] + "▮▮▮▮▮▮▮▮▮▮"
            await callback.message.edit_text(text=msg, parse_mode="HTML", reply_markup=markup.to_platforms)

            logger.debug("Архивы отправлены")

            shutil.rmtree(dst, ignore_errors=True)
            if archive_path.exists():
                os.remove(archive_path)
            logger.debug("Временные архивы удалены")


        except Exception as e:
            logger.error(e, exc_info=True)

    elif "android" in callback.data:
        try:

            user_config = await utils.get_link(chat_id, "Android")

            routing_rules = '[{"enabled":true,"ip":["geoip:ru"],"looked":false,"outboundTag":"direct","remarks":"geoip direct"},{"domain":["geosite:category-gov-ru","geosite:yandex","geosite:vk","regexp:xn--"],"enabled":true,"looked":false,"outboundTag":"direct","remarks":"geosite direct"},{"domain":["geosite:category-ads-all"],"enabled":true,"looked":false,"outboundTag":"block","remarks":"ads block"},{"enabled":true,"ip":["geoip:private"],"looked":false,"outboundTag":"direct","remarks":"geoip private"},{"domain":["geosite:private"],"enabled":true,"looked":false,"outboundTag":"direct","remarks":"geosite private"}]'

            await callback.message.answer(
                text="Порядок установки VPN на android:\n\n"
                "1. Откройте ссылку: https://drive.google.com/file/d/1MsrZp13yQUGQHRZIAJHYU6CdSQIwffel/view?usp=sharing \n" \
                "2. Загрузите файл <u>v2rayNG_1.10.23.apk</u> с диска\n" \
                "3. Откройте этот файл и установите приложение\n" \
                "4. Следуйте инструкциям отсюда: https://teletype.in/@kn1ver/Android-install \n\n" \
                "Ресурсы:\n" \
                f"<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                f"<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>",
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(e, exc_info=True)

    elif "ios" in callback.data:
        try:

            user_config = await utils.get_link(chat_id, "IOS")

            routing_rules = 'v2box://routes?multi=W3siZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cnUiXSwibG9ja2VkIjpmYWxzZSwib3V0Ym91bmRUYWciOiJkaXJlY3QiLCJyZW1hcmtzIjoiZ2VvaXAgZGlyZWN0In0seyJkb21haW4iOlsiZ2Vvc2l0ZTpjYXRlZ29yeS1nb3YtcnUiLCJnZW9zaXRlOnlhbmRleCIsImdlb3NpdGU6dmsiLCJyZWdleHA6eG4tLSJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9zaXRlIGRpcmVjdCJ9LHsiZG9tYWluIjpbImdlb3NpdGU6Y2F0ZWdvcnktYWRzLWFsbCJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImJsb2NrIiwicmVtYXJrcyI6ImFkcyBibG9jayJ9LHsiZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cHJpdmF0ZSJdLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9pcCBwcml2YXRlIn0seyJkb21haW4iOlsiZ2Vvc2l0ZTpwcml2YXRlIl0sImVuYWJsZWQiOnRydWUsImxvY2tlZCI6ZmFsc2UsIm91dGJvdW5kVGFnIjoiZGlyZWN0IiwicmVtYXJrcyI6Imdlb3NpdGUgcHJpdmF0ZSJ9XQ=='

            await callback.message.answer(
                text="Для установки настройки VPN\nСледуйте инструкциям отсюда: https://teletype.in/@kn1ver/install-ios \n\n" \
                "Ресурсы:\n" \
                f"<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                f"<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>",
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(e, exc_info=True)
