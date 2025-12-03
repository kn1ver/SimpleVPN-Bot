import os
import random
import shutil
import time

import app.keyboards as markup
from config import MESSAGES as msg_text, XUI_INBOUND_ID
from config import ROUTING_RULES as routing_rules
from utils.logger import logger
from utils import xui
from utils import sqlite as db
from utils import utils as utils

from datetime import datetime, timedelta
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery, FSInputFile, LabeledPrice, InputMediaPhoto

router_main = Router()
class states (StatesGroup):
    problem = State()
    payment = State()

@router_main.message(Command('key'))
async def command_key(message: Message, state: FSMContext):
    await state.clear()
    xui_data = xui.get_user_data(str(message.chat.id))
    xui_id = xui_data["PC"]["id"] if xui_data["PC"]["enable"] else msg_text["paid_0"]
    await message.answer(
        text=f'Ваш ключ активации:\n<span class="tg-spoiler">{xui_id}</span>',
        parse_mode="HTML"
    )

@router_main.message(Command('profile'))
async def command_profile(message: Message, state: FSMContext):
    try:
        await state.clear()

        user_id = message.chat.id
        client = xui.get_user_data(str(user_id))
        logger.debug(f"profile | xui.get_user_data:\n{client}\n\n")

        if not client or not client["PC"]["enable"]:
            await message.answer(
                text=msg_text["paid_0"],
                reply_markup=markup.pay_vpn
            )
            return

        platform_messages = []
        platforms = ["PC", "Android", "IOS"]
        for platform in platforms:
            platform_message = msg_text["profile_platform"].format(
                platform=platform,
                enable='✅ Да' if client[platform]['enable'] else '🔴 Нет',
                online='🟢 Онлайн' if client[platform]['online'] else '🔴 Офлайн',
                down=client[platform]['down'],
                up=client[platform]['up'],
                expiry=client[platform]['expiryTime']
            ) if client[platform] else ""
            platform_messages.append(platform_message)

        msg = f"Ваши устройства:\n\n{"".join(platform_messages)}"

        await message.answer(
            text=msg,
            reply_markup=markup.to_main,
            parse_mode="HTML"
        )

    except Exception as e:
        if e != KeyError:
            logger.error(e, exc_info=1)

@router_main.message(Command('support'))
async def command_support(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer(
            text=msg_text["help"],
            reply_markup=markup.to_main
        )
        await state.set_state(states.problem)

    except Exception as e: logger.error(e, exc_info=1)

@router_main.message(Command('set_expiryTime'))
async def set_expiryTime(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    if message.chat.id == 1616183086:
        msg = message.text
        chat_id = msg.split(" ")[1]
        expiryTime_days = msg.split(" ")[2]

        expiryTime_ms = int(time.time()) * 1000 + int(expiryTime_days) * 24 * 3600 * 1000

        await db.set_user_data("chat_id", chat_id, "expires_at", expiryTime_ms)
        xui.update_client_expiry(1, chat_id, int(expiryTime_days),logger)
        await message.answer(f"Для пользователя {chat_id} установлено expiryTime: {expiryTime_days} дней")
        logger.debug(f"Для пользователя {chat_id} установлено expiryTime: {expiryTime_days} дней")
    return

@router_main.message(Command('start'))
async def start (message: Message, bot: Bot, state: FSMContext):
    try:
        msg = msg_text["main_menu"]
        user_id = message.chat.id
        
        await state.clear()
        await message.answer(
            text=msg,
            reply_markup=markup.start
        )

        await db.create_db()
        try:
            await db.reg_user(str(user_id))
        except Exception as e:
            if not ("UNIQUE constraint failed" in str(e)):
                logger.error(f"Не удалось зарегистрировать пользователя {user_id}: {e}", exc_info=1)

        await bot.send_message(
            chat_id=1616183086,
            text=f'Пользователь {message.from_user.full_name} | @{message.from_user.username} | {user_id} открыл бота'
        )

    except Exception as e: logger.error(e, exc_info=1)



@router_main.callback_query(lambda c: "profile" in c.data)
async def profile(callback: CallbackQuery, bot: Bot):
    try:
        user_id = callback.message.chat.id
        client = xui.get_user_data(str(user_id))
        logger.debug(f"profile | xui.get_user_data:\n{client}\n\n")

        if not client or not client["PC"]["enable"]:
            await callback.message.edit_text(
                text=msg_text["paid_0"],
                reply_markup=markup.pay_vpn
            )

        platform_messages = []
        platforms = ["PC", "Android", "IOS"]
        for platform in platforms:
            platform_message = msg_text["profile_platform"].format(
                platform=platform,
                enable='✅ Да' if client[platform]['enable'] else '🔴 Нет',
                online='🟢 Онлайн' if client[platform]['online'] else '🔴 Офлайн',
                down=client[platform]['down'],
                up=client[platform]['up'],
                expiry=client[platform]['expiryTime']
            ) if client[platform] else ""
            platform_messages.append(platform_message)

        msg = f"Ваши устройства:\n\n{"".join(platform_messages)}"

        await callback.message.edit_text(
            text=msg,
            reply_markup=markup.to_main,
            parse_mode="HTML"
        )

    except Exception as e:
        if e != KeyError:
            logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "return" in c.data)
async def return_to(callback: CallbackQuery, bot: Bot, state: FSMContext):
    try:
        await state.clear()

        if "main" in callback.data:
            msg = msg_text["main_menu"]
            reply_mk = markup.start

        elif "platforms" in callback.data:
            msg = msg_text["platforms"]
            reply_mk = markup.platforms

        await callback.message.edit_text(
            text=msg,
            reply_markup=reply_mk
        )

    except Exception as e: logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "install" in c.data)
async def install_vpn(callback: CallbackQuery, bot: Bot):
    try:
        user_id = callback.message.chat.id

        if "vpn" in callback.data:
            user_paid = await db.get_user_data("chat_id", str(user_id), ["paid"])

            if not user_paid[0][0]:
                await callback.message.edit_text(
                    text=msg_text["paid_0"],
                    reply_markup=markup.pay_vpn
                )
                return

            await callback.message.edit_text(
                text=msg_text["platforms"],
                reply_markup=markup.platforms
            )

        elif "pc" in callback.data:
            xui_data = xui.get_user_data(str(user_id))
            xui_id = xui_data["PC"]["id"]
            msg = msg_text["platforms_pc"].format(xui_id=xui_id)

            if "get_installer" in callback.data:
                installer = FSInputFile("files/installer.exe")

                await callback.message.answer_document(installer)
                
            else:
                await callback.message.edit_text(
                    text=msg,
                    reply_markup=markup.pc,
                    parse_mode="HTML"
                )

        elif "android" in callback.data:
            if "get_settings" in callback.data:
                settings_file = FSInputFile("files/nekobox_settings.json")
                await callback.message.answer_document(settings_file)
                return

            user_config = await utils.get_link(str(user_id), "Android")
            msg = msg_text["platforms_adnroid"].format(
                user_config=user_config,
                routing_rules=routing_rules["adnroid"]
            )

            await callback.message.edit_text(
                text=msg,
                parse_mode="HTML",
                reply_markup=markup.adnroid
            )

        elif "ios" in callback.data:
            user_config = await utils.get_link(str(user_id), "IOS")
            msg = msg_text["platforms_ios"].format(
                user_config=user_config,
                routing_rules=routing_rules["ios"]
            )

            await callback.message.edit_text(
                text=msg,
                parse_mode="HTML",
                reply_markup=markup.to_platforms
            )
    
    except Exception as e: logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "pay_" in c.data or "buy" in c.data)
async def pay_vpn(callback: CallbackQuery, bot: Bot, state: FSMContext):
    try:
        user_id = callback.message.chat.id
        if "pay_" in callback.data:
            msg = msg_text["pay_conditions"]

            await callback.message.edit_text(
                text=msg,
                parse_mode="HTML",
                reply_markup=markup.buy_vpn
            )

        elif "buy" in callback.data:
            expires_old_ms = await db.get_user_data("chat_id", str(user_id), ["expires_at"])
            expires_old_ms = expires_old_ms[0][0] if expires_old_ms else None

            if expires_old_ms:
                expires_old_datetime = datetime.utcfromtimestamp(expires_old_ms/1000)
                time_left = expires_old_datetime - datetime.utcnow()
            else:
                time_left = None

            if time_left and time_left > timedelta(days=7):
                await callback.message.edit_text(
                    text=msg_text["sub_already_connected"],
                    reply_markup=markup.to_main
                )
                return

            msg = msg_text["pay_details"]

            await callback.message.edit_text(
                text=msg,
                parse_mode="HTML",
                reply_markup=markup.to_main
            )

            await state.set_state(states.payment)
            return
    
    except Exception as e: logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "help" in c.data)
async def help(callback: CallbackQuery, state: FSMContext):
    try:

        await callback.message.edit_text(
            text=msg_text["help"],
            reply_markup=markup.to_main
        )
        await state.set_state(states.problem)

    except Exception as e: logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "payment" in c.data)
async def payment_action(callback: CallbackQuery, bot: Bot):
    user_id = callback.data.split("_")[-1]

    approve_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Подтверждено', callback_data='None')]])
    deny_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отклонено', callback_data='None')]])

    try:
        if "approve" in callback.data:
            await callback.message.edit_reply_markup(reply_markup=approve_markup)
            await bot.send_message(
                chat_id=user_id,
                text=msg_text["payment_approved"]
            )

            expires_old_ms = await db.get_user_data("chat_id", user_id, ["expires_at"])
            expires_old_ms = expires_old_ms[0][0] if expires_old_ms else None

            if expires_old_ms:
                expires_old_datetime = datetime.utcfromtimestamp(expires_old_ms/1000)
                time_left = expires_old_datetime - datetime.utcnow()

                if time_left.total_seconds() >= 0:
                    logger.debug(f"payment_action -> approve | {user_id}: Продление текущей подписки")

                    expires_new = expires_old_ms + 31 * 24 * 3600 * 1000

                    await db.set_user_data("chat_id", user_id, "bought_at", expires_old_ms)
                    await db.set_user_data("chat_id", user_id, "expires_at", expires_new)
                    xui.update_client_expiry(XUI_INBOUND_ID, user_id, 31, logger)

                    msg = msg_text["sub_renewed"].format(
                        expires_at=utils.parse_expiry_time(expires_new, "%d.%m.%y")
                    )
                    await bot.send_message(
                        chat_id=user_id,
                        text=msg
                    )
                
            if not expires_old_ms or time_left.total_seconds() < 0:
                logger.debug(f"payment_action -> approve | {user_id}: Оплата новой подписки")

                now = int(time.time()) * 1000
                expires_at = now + 31 * 24 * 3600 * 1000

                xui.reg_user_connection(user_id, expires_at)
                xui_id = xui.get_user_data(user_id)["PC"]["id"]

                await db.set_user_data("chat_id", user_id, "paid", 1)
                await db.set_user_data("chat_id", user_id, "xui_id", str(xui_id))
                await db.set_user_data("chat_id", user_id, "bought_at", now)
                await db.set_user_data("chat_id", user_id, "expires_at", expires_at)

                msg = msg_text["sub_connected"].format(
                    expires_at=utils.parse_expiry_time(expires_at, "%d.%m.%y")
                )

                await bot.send_message(chat_id=user_id, text=msg)

        elif "deny" in callback.data:
            await callback.message.edit_reply_markup(reply_markup=deny_markup)
            await bot.send_message(
                chat_id=user_id,
                text=msg_text["payment_deny"]
            )

    except Exception as e: logger.debug(e, exc_info=1)



@router_main.message(states.problem)
async def problem(message: Message, bot: Bot):
    try:
        user_id = message.chat.id

        user_msg_text = message.text if message.text else ""
        msg_caption = message.caption if message.caption else ""
        photo = message.photo[-1] if message.photo else False
        document = message.document if message.document else False

        user_data = f"@{message.from_user.username} | {user_id}" 
        msg = user_data + "\n\n" + msg_caption if msg_caption else user_data + "\n\n" + user_msg_text

        if photo:
            # сохраняем фото
            photo_id = photo.file_id
            photo_info = await bot.get_file(photo_id) # получаем само фото с серверов ТГ по id

            downloaded_photo = await bot.download_file(photo_info.file_path) # сохраняем фото в переменную
            photo_path = os.path.join("files", "temp", f"{user_id}_{random.randint(0, 999)}.jpg") # определяем путь, куда сохранится фото

            with open (photo_path, 'wb') as photo:
                photo.write(downloaded_photo.read()) # сохраняем фото по указанному пути
            logger.debug(f"problem | {user_id}: изображение сохранено")

            # отправляем сообщение админу
            await bot.send_photo(
                chat_id=1616183086,
                photo=FSInputFile(photo_path),
                caption=msg
            )
            logger.debug(f"problem | {user_id}: изображение отправлено")

            # удаляем фото
            os.remove(photo_path)
            logger.debug(f"problem | {user_id}: изображение удалено")
        
        elif document:

            # сохраняем документ
            document_id = document.file_id
            document_info = await bot.get_file(document_id)
            document_ext = dict(document_info)['file_path'].split('/')[-1].split('.')[-1]

            downloaded_document = await bot.download_file(document_info.file_path)
            document_path = os.path.join("files", "temp", f"{user_id}_{random.randint(0, 999)}.{document_ext}")

            with open (document_path, 'wb') as document:
                document.write(downloaded_document.read())
            logger.debug(f"problem | {user_id}: документ сохранен")

            # отправляем документ админу
            await bot.send_document(
                chat_id=1616183086,
                document=FSInputFile(document_path),
                caption=msg)
            logger.debug(f"problem | {user_id}: документ отправлен")

            # удаляем документ
            os.remove(document_path)
            logger.debug(f"problem | {user_id}: документ удален")

        else:
            await bot.send_message(
                chat_id=1616183086,
                text=msg
            )

        await message.answer(
            text=msg_text["problem_accepted"],
            parse_mode="HTML",
            reply_markup=markup.to_main
        )

    except Exception as e: logger.error(e, exc_info=1)

@router_main.message(states.payment)
async def approve_payment(message: Message, bot: Bot, state: FSMContext):
    try:
        photo = message.photo[-1]
    except Exception as e:
        photo = None
    caption = message.caption if message.caption else ""
    user_id = message.chat.id
    admin_msg = f"{datetime.now()} | {user_id} | @{message.from_user.username}\n"

    if not photo:
        await message.answer(text=msg_text["without_photo"])
        await state.set_state(states.payment)
        return
    
    else:
        await message.answer(text=msg_text["found_scrnShot"])

        # сохраняем фото
        photo_id = photo.file_id
        photo_info = await bot.get_file(photo_id) # получаем само фото с серверов ТГ по id

        downloaded_photo = await bot.download_file(photo_info.file_path) # сохраняем фото в переменную
        photo_path = os.path.join("files", "temp", f"{user_id}_{random.randint(0, 999)}.jpg") # определяем путь, куда сохранится фото

        with open (photo_path, 'wb') as photo:
            photo.write(downloaded_photo.read()) # сохраняем фото по указанному пути
        logger.debug(f"approve_payment | {user_id}: изображение сохранено")

        # отправляем сообщение админу
        await bot.send_photo(
            chat_id=1616183086,
            photo=FSInputFile(photo_path),
            caption=admin_msg + caption,
            reply_markup=markup.approve_payment(str(user_id)))
        logger.debug(f"approve_payment | {user_id}: изображение отправлено")

        # удаляем фото
        os.remove(photo_path)
        logger.debug(f"approve_payment | {user_id}: изображение удалено") 

    
