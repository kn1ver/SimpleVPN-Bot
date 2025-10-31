import app.keyboards as markup
import os
import random
import shutil
import time

from utils.logger import logger
from utils import xui
from utils import sqlite as db
from utils import utils as utils

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, LabeledPrice, InputMediaPhoto

router_main = Router()
class states (StatesGroup):
    problem = State()

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

        # await bot.send_message(
        #     chat_id=1616183086,
        #     text=f'Пользователь {message.from_user.full_name} | @{message.from_user.username} | {message.chat.id} открыл бота')
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
async def return_to(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
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
                    f"Ваш ключ доступа: <code>{xui_id}</code>\n\n Архивы отправляются ▯▯▯▯▯▯▯▯▯▯"

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

@router_main.callback_query(lambda c: "pay" in c.data or "buy" in c.data)
async def pay_vpn(callback: CallbackQuery, bot: Bot):
    if "pay" in callback.data:
        try:

            msg = (
                "🌐 После оплаты вы получаете полный доступ к <b>SimpleVPN</b>.\n" \
                "Установить его можно на <b>Android, ПК и iOS</b> — по одному устройству для каждой платформы.\n\n" \
                "💳 Стоимость подписки всего <i><b>200</b>руб за <b>31</b> день</i>\n" \
                "Мы честно напомним о платеже за <b>7 и 3 дня</b>, чтобы вы успели решить, остаёмся ли вместе дальше.\n" \
                "✨ Никаких скрытых списаний"
            )

            await callback.message.edit_text(text=msg, parse_mode="HTML", reply_markup=markup.buy_vpn)

        except Exception as e:
            logger.error(e)

    elif "buy" in callback.data:
        try:

            await callback.message.answer(text="Оплата не доступна на данный момент.")

            if callback.message.chat.id != 1616183086:
                return

            # TODO что делаем после оплаты
            #
            # регаем юзера в xui (выполнено)
            # регаем юзера в sqlite (выполнено)
            #
            # рассчитывать сроки списания и тп (частично) ->
            # -> продумать продление подписки (в процессе)
            #
            # вынести все сообщения в отдельный файл
            # сообщение в главном меню после "назад" отличается от того же после "/start"

            user_id = str(callback.message.chat.id)
            xui.reg_user_connection(user_id)
            xui_id = xui.get_user_data(user_id)["PC"]["id"]

            now = int(time.time())
            expires = now + 31 * 24 * 3600

            await db.set_user_data("chat_id", user_id, "paid", 1)
            await db.set_user_data("chat_id", user_id, "xui_id", str(xui_id))
            await db.set_user_data("chat_id", user_id, "bought_at", now)
            await db.set_user_data("chat_id", user_id, "expires_at", expires)

            msg = (
                "Подписка подключена. Спасибо за покупку!"
                f"Истекает: {expires}"
                'Перейдите в раздел "Установить VPN" для установки.'
            )

            await callback.message.answer(text=msg)

        except Exception as e:
            logger.error(e)

@router_main.callback_query(lambda c: "help" in c.data)
async def help(callback: CallbackQuery, state: FSMContext):
    try:

        await callback.message.answer(
            text="Как можно подробнее опишите проблему, с которой вы столкнулись, в ответном сообщении. Мы постараемся помочь вам как можно быстрее\n(Вы можете приложить до 1 фотографии/файла)",
            reply_markup=markup.to_main
        )
        await state.set_state(states.problem)

    except Exception as e:
        logger.error(e)


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

    except Exception as e:
        logger.error(e, exc_info=True)
