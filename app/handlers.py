import app.keyboards as markup
import os
import random
import shutil
import time

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

@router_main.message(Command('set_expiryTime'))
async def set_expiryTime(message: Message, bot: Bot, state: FSMContext):
    if message.chat.id == 1616183086:
        msg = message.text
        chat_id = msg.split(" ")[1]
        expiryTime_days = msg.split(" ")[2]

        expiryTime_ms = int(time.time()) * 1000 + int(expiryTime_days) * 24 * 3600 * 1000

        await db.set_user_data("chat_id", chat_id, "expires_at", expiryTime_ms)
        xui.update_client_expiry(1, chat_id, int(expiryTime_days),logger)
        logger.debug(f"Для пользователя {chat_id} установлено expiryTime: {expiryTime_days} дней")
    return

@router_main.message(Command('start'))
async def start (message: Message, bot: Bot, state: FSMContext):
    try:
        await state.clear()
        await message.answer(
            text='🚀 Добро пожаловать в SimpleVPN!\nБезопасный и быстрый интернет без отслеживания и скрытых списаний',
            reply_markup=markup.start
            )

        try:
            await db.create_db()
        except:
            pass

        try:
            await db.reg_user(str(message.chat.id))
        except Exception as e:
            logger.error(f"Не удалось зарегистрировать пользователя {message.chat.id}: {e}")

        await bot.send_message(
            chat_id=1616183086,
            text=f'Пользователь {message.from_user.full_name} | @{message.from_user.username} | {message.chat.id} открыл бота')
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
            f"📅 Окончание: {client["PC"]["expiryTime"]}\n\n"
        ) if client["PC"] else ""

        msg_android = (
            f"<b>   Andoid\n</b>"
            f"💡Активен: {'✅ Да' if client["Android"]['enable'] else '🔴 Нет'}\n"
            f"🌐 Статус соединения: {'🟢 Онлайн' if client["Android"]['online'] else '🔴 Офлайн'}\n"
            f"🔼 Загрузка: {client["Android"]["up"]}\n🔽 Скачивание: {client["Android"]["down"]}\n"
            f"📅 Окончание: {client["Android"]["expiryTime"]}\n\n"
        ) if client["Android"] else ""

        msg_ios = (
            f"<b>   IOS\n</b>"
            f"💡Активен: {'✅ Да' if client["IOS"]['enable'] else '🔴 Нет'}\n"
            f"🌐 Статус соединения: {'🟢 Онлайн' if client["IOS"]['online'] else '🔴 Офлайн'}\n"
            f"🔼 Загрузка: {client["IOS"]["up"]}\n🔽 Скачивание: {client["IOS"]["down"]}\n"
            f"📅 Окончание: {client["IOS"]["expiryTime"]}\n\n"
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
async def return_to(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    try:
        if "main" in callback.data:
            await callback.message.edit_text(
                text='🚀 Добро пожаловать в SimpleVPN!\nБезопасный и быстрый интернет без отслеживания и скрытых списаний',
                reply_markup=markup.start)

        elif "platforms" in callback.data:
            await callback.message.edit_text(text='На какую платформу Вы хотите установить VPN?', reply_markup=markup.platforms)

    except Exception as e:
        logger.error(e)

@router_main.callback_query(lambda c: "install" in c.data)
async def install_vpn(callback: CallbackQuery, bot: Bot):

    chat_id = str(callback.message.chat.id)

    if "vpn" in callback.data:
        try:

            user_paid = await db.get_user_data("chat_id", str(chat_id), ["paid"])

            if not user_paid[0][0]:
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
            xui_id = xui_data["PC"]["id"]
            msg = "С порядоком установки VPN на компьютер вы можете ознакомиться по этой ссылке:\n" \
                    "https://teletype.in/@kn1ver/install-pc \n\n" \
                    f"<b>Ваш ключ активации</b>: <code>{xui_id}</code>\n\n Архивы отправляются ▯▯▯▯▯▯▯▯▯▯"

            msg_id = await callback.message.edit_text(
                text=msg,
                reply_markup=markup.to_platforms,
                parse_mode="HTML")

            archive, dll, dst, archive_path = await utils.get_archive(chat_id, bot, int(msg_id.message_id))
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

            await callback.message.edit_text(
                text="Порядок установки VPN на android:\n\n"
                "1. Откройте ссылку: https://drive.google.com/file/d/1MsrZp13yQUGQHRZIAJHYU6CdSQIwffel/view?usp=sharing \n" \
                "2. Загрузите файл <u>v2rayNG_1.10.23.apk</u> с диска\n" \
                "3. Откройте этот файл и установите приложение\n" \
                "4. Следуйте инструкциям отсюда: https://teletype.in/@kn1ver/Android-install \n\n" \
                "Ресурсы:\n" \
                f"<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                f"<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>",
                parse_mode="HTML",
                reply_markup=markup.to_platforms
            )

        except Exception as e:
            logger.error(e, exc_info=True)

    elif "ios" in callback.data:
        try:

            user_config = await utils.get_link(chat_id, "IOS")

            routing_rules = 'v2box://routes?multi=W3siZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cnUiXSwibG9ja2VkIjpmYWxzZSwib3V0Ym91bmRUYWciOiJkaXJlY3QiLCJyZW1hcmtzIjoiZ2VvaXAgZGlyZWN0In0seyJkb21haW4iOlsiZ2Vvc2l0ZTpjYXRlZ29yeS1nb3YtcnUiLCJnZW9zaXRlOnlhbmRleCIsImdlb3NpdGU6dmsiLCJyZWdleHA6eG4tLSJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9zaXRlIGRpcmVjdCJ9LHsiZG9tYWluIjpbImdlb3NpdGU6Y2F0ZWdvcnktYWRzLWFsbCJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImJsb2NrIiwicmVtYXJrcyI6ImFkcyBibG9jayJ9LHsiZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cHJpdmF0ZSJdLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9pcCBwcml2YXRlIn0seyJkb21haW4iOlsiZ2Vvc2l0ZTpwcml2YXRlIl0sImVuYWJsZWQiOnRydWUsImxvY2tlZCI6ZmFsc2UsIm91dGJvdW5kVGFnIjoiZGlyZWN0IiwicmVtYXJrcyI6Imdlb3NpdGUgcHJpdmF0ZSJ9XQ=='

            await callback.message.edit_text(
                text="Для установки настройки VPN\nСледуйте инструкциям отсюда: https://teletype.in/@kn1ver/install-ios \n\n" \
                "Ресурсы:\n" \
                f"<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                f"<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>",
                parse_mode="HTML",
                reply_markup=markup.to_platforms
            )

        except Exception as e: logger.error(e, exc_info=True)

@router_main.callback_query(lambda c: "pay_" in c.data or "buy" in c.data)
async def pay_vpn(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if "pay_" in callback.data:
        try:

            msg = (
                "🌐 После оплаты вы получаете полный доступ к <b>SimpleVPN</b>.\n" \
                "Установить его можно на <b>Android, ПК и iOS</b> — по одному устройству для каждой платформы.\n\n" \
                "💳 Стоимость подписки всего <i><b>200</b>руб за <b>31</b> день</i>\n" \
                "Мы честно напомним о платеже за <b>7 и 3 дня</b>, чтобы вы успели решить, остаёмся ли вместе дальше.\n" \
                "✨ Никаких скрытых списаний"
            )

            await callback.message.edit_text(text=msg, parse_mode="HTML", reply_markup=markup.buy_vpn)

        except Exception as e: logger.error(e, exc_info=1)

    elif "buy" in callback.data:
        try:
            user_id = str(callback.message.chat.id)
            expires_old_ms = await db.get_user_data("chat_id", user_id, ["expires_at"])
            expires_old_ms = expires_old_ms[0][0] if expires_old_ms else None

            if expires_old_ms:
                expires_old_datetime = datetime.utcfromtimestamp(expires_old_ms/1000)
                time_left = expires_old_datetime - datetime.utcnow()
            else:
                time_left = None

            if time_left and time_left > timedelta(days=7):
                await callback.message.edit_text(
                    text="У вас уже есть действующая подписка\nПродлить её будет можно за 7 дней до окончания текущего периода",
                    reply_markup=markup.to_main
                )
                return

            msg = (
            "Для оплаты подписки переведите деньги по следующим реквизитам:\n"

            "    Номер карты: <code>2200700893574078</code>\n"
            "    Номер телефона: <code>89397136806</code>\n"
            "    Банк: ТБанк\n"

            "    Сумма: 200 рублей\n"

            "После оплаты отправьте скриншот о переводе в этот чат."
            )

            await callback.message.edit_text(
                text=msg,
                reply_markup=markup.to_main,
                parse_mode="HTML"
            )

            await state.set_state(states.payment)
            return
    
        except Exception as e: logger.error(e, exc_info=1)

@router_main.callback_query(lambda c: "help" in c.data)
async def help(callback: CallbackQuery, state: FSMContext):
    try:

        await callback.message.edit_text(
            text="Как можно подробнее опишите проблему, с которой вы столкнулись, в ответном сообщении. Мы постараемся помочь вам как можно быстрее\n(Вы можете приложить до 1 фотографии/файла)",
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
                text="Оплата подписки была подтверждена")

            expires_old_ms = await db.get_user_data("chat_id", user_id, ["expires_at"])
            expires_old_ms = expires_old_ms[0][0] if expires_old_ms else None

            if expires_old_ms:
                expires_old_datetime = datetime.utcfromtimestamp(expires_old_ms/1000)
                time_left = expires_old_datetime - datetime.utcnow()

                if time_left.total_seconds() >= 0:
                    logger.debug("*Продление текущей подписки invoice*")

                    expires_new = expires_old_ms + 31 * 24 * 3600 * 1000

                    await db.set_user_data("chat_id", user_id, "bought_at", expires_old_ms)
                    await db.set_user_data("chat_id", user_id, "expires_at", expires_new)
                    xui.update_client_expiry(1, user_id, 31, logger)

                    msg = (
                        "Подписка продлена. Спасибо за покупку!\n"
                        f"Истекает: {utils.parse_expiry_time(expires_new, "%d.%m.%y")}\n")
                    await bot.send_message(chat_id=user_id, text=msg)
                
            if not expires_old_ms or time_left.total_seconds() < 0:
                logger.debug("*Оплата новой подписки invoice*")

                now = int(time.time()) * 1000
                expires = now + 31 * 24 * 3600 * 1000

                xui.reg_user_connection(user_id, expires)
                xui_id = xui.get_user_data(user_id)["PC"]["id"]

                await db.set_user_data("chat_id", user_id, "paid", 1)
                await db.set_user_data("chat_id", user_id, "xui_id", str(xui_id))
                await db.set_user_data("chat_id", user_id, "bought_at", now)
                await db.set_user_data("chat_id", user_id, "expires_at", expires)

                msg = (
                    "Подписка подключена. Спасибо за покупку!\n"
                    f"Истекает: {utils.parse_expiry_time(expires, "%d.%m.%y")}\n"
                    'Перейдите в раздел "Установить VPN" для установки.')

                await bot.send_message(chat_id=user_id, text=msg)

        elif "deny" in callback.data:
            await callback.message.edit_reply_markup(reply_markup=deny_markup)
            await bot.send_message(chat_id=user_id, text='Оплата подписки была отклонена. Вы можете спросить о причинах в разделе "Поддрежка"')

    except Exception as e: logger.debug(e, exc_info=True)



@router_main.message(states.problem)
async def problem(message: Message, bot: Bot):
    try:
        chat_id = message.chat.id

        msg_text = message.text if message.text else ""
        msg_caption = message.caption if message.caption else ""
        photo = message.photo[-1] if message.photo else False
        document = message.document if message.document else False

        user_data = f"@{message.from_user.username} | {message.chat.id}" 
        msg = user_data + "\n\n" + msg_caption if msg_caption else user_data + "\n\n" + msg_text

        if photo:
            # сохраняем фото
            photo_id = photo.file_id
            photo_info = await bot.get_file(photo_id) # получаем само фото с серверов ТГ по id

            downloaded_photo = await bot.download_file(photo_info.file_path) # сохраняем фото в переменную
            photo_path = os.path.join("files", "temp", f"{message.chat.id}_{random.randint(0, 999)}.jpg") # определяем путь, куда сохранится фото

            with open (photo_path, 'wb') as photo:
                photo.write(downloaded_photo.read()) # сохраняем фото по указанному пути
            logger.debug(f"изображение {chat_id} сохранено")

            # отправляем сообщение админу
            await bot.send_photo(
                chat_id=1616183086,
                photo=FSInputFile(photo_path),
                caption=msg)
            logger.debug(f"изображение {chat_id} отправлено")

            # удаляем фото
            os.remove(photo_path)
            logger.debug(f"изображение {chat_id} удалено")
        
        elif document:

            # сохраняем документ
            document_id = document.file_id
            document_info = await bot.get_file(document_id)
            document_ext = dict(document_info)['file_path'].split('/')[-1].split('.')[-1]

            downloaded_document = await bot.download_file(document_info.file_path)
            document_path = os.path.join("files", "temp", f"{message.chat.id}_{random.randint(0, 999)}.{document_ext}")

            with open (document_path, 'wb') as document:
                document.write(downloaded_document.read())
            logger.debug(f"документ {chat_id} сохранен")

            # отправляем документ админу
            await bot.send_document(
                chat_id=1616183086,
                document=FSInputFile(document_path),
                caption=msg)
            logger.debug(f"документ {chat_id} отправлен")

            # удаляем документ
            os.remove(document_path)
            logger.debug(f"документ {chat_id} удален")

        else:
            await bot.send_message(
                chat_id=1616183086,
                text=msg)

        await message.answer(text="Сообщение доставлено. В скором времени с вами свяжится поддержка.\nВы можете дополнить обращение, отправив детали сюда же")

    except Exception as e: logger.error(e, exc_info=True)

@router_main.message(states.payment)
async def approve_payment(message: Message, bot: Bot, state: FSMContext):
    try:
        photo = message.photo[-1]
    except Exception as e:
        photo = None
    caption = message.caption if message.caption else ""
    chat_id = str(message.chat.id)
    admin_msg = f"{datetime.now()} | {chat_id} | @{message.from_user.username}\n"

    if not photo:
        await message.answer("В сообщении не обнаружено фото\nДля подтверждения оплаты отправьте скриншот из банка")
        await state.set_state(states.payment)
        return
    else:
        await message.answer("Подписка будет оплачена, когда администратор подтвердит перевод. Вы будете оповещены\nСпасибо, что выбрали SimpleVPN")

        # сохраняем фото
        photo_id = photo.file_id
        photo_info = await bot.get_file(photo_id) # получаем само фото с серверов ТГ по id

        downloaded_photo = await bot.download_file(photo_info.file_path) # сохраняем фото в переменную
        photo_path = os.path.join("files", "temp", f"{chat_id}_{random.randint(0, 999)}.jpg") # определяем путь, куда сохранится фото

        with open (photo_path, 'wb') as photo:
            photo.write(downloaded_photo.read()) # сохраняем фото по указанному пути
        logger.debug(f"изображение {chat_id} сохранено")

        # отправляем сообщение админу
        await bot.send_photo(
            chat_id=1616183086,
            photo=FSInputFile(photo_path),
            caption=admin_msg + caption,
            reply_markup=markup.approve_payment(chat_id))
        logger.debug(f"изображение {chat_id} отправлено")

        # удаляем фото
        os.remove(photo_path)
        logger.debug(f"изображение {chat_id} удалено") 

    
