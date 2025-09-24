from aiogram.types import FSInputFile
from aiogram import Bot
from datetime import datetime
from utils.logger import logger
from utils import xui
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

import shutil
import json
import hashlib
import random

BASE_DIR = Path(__file__).resolve().parent.parent  # поднимаемся из utils/ в корень проекта
FILES_DIR = BASE_DIR / "files"

def size_parser(num_bytes: int) -> str:
    """
    Переводит размер из байтов в наиболее удобную единицу (KB, MB, GB, TB).
    Возвращает строку с 2 знаками после запятой.
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def parse_expiry_time(expiry_time: int) -> str:
    """
    Преобразует expiryTime (в миллисекундах) в удобную дату/время.
    """
    if not expiry_time or expiry_time == 0:
        return "Без ограничения"

    # expiryTime приходит в миллисекундах -> делим на 1000
    dt = datetime.fromtimestamp(expiry_time / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def encrypt_json(data: dict, key: bytes) -> bytes:
    """Шифрует JSON-словарь и возвращает бинарные данные"""
    plaintext = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")

    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    # возвращаем iv + данные
    return iv + ciphertext

def decrypt_json(encrypted_data: bytes, key: bytes) -> dict:
    """Расшифровывает бинарные данные обратно в JSON"""
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

    return json.loads(plaintext.decode("utf-8"))

async def add_user_xui(email: str):
    pass

async def get_archive(user_id: str, bot: Bot, msg_id: int, access_key):
    xui_data = xui.get_user_data(user_id)
    xui_id = xui_data["PC"]["id"]
    aes_key = hashlib.sha256(str(xui_id).encode("utf-8")).digest()
    chat_id = user_id
    randint = random.randint(0, 1000)
    msg = "С порядоком установки VPN на компьютер вы можете ознакомиться по этой ссылке:\n" \
            "https://teletype.in/@kn1ver/install-pc \n\n" \
            f"Ваш ключ доступа: <code>{access_key}</code>\n\n Архивы отправляются ▯▯▯▯▯▯▯▯▯▯"

    src = FILES_DIR / "nekoray"
    dst = FILES_DIR / "temp" / f"nekoray_{user_id}_{randint}"

    shutil.copytree(src, dst, dirs_exist_ok=True)
    msg = msg[:-10] + "▮▯▯▯▯▯▯▯▯▯"
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=msg,
        parse_mode="HTML"
    )
    logger.debug("Папка nekoray скопирована")

    # читаем и изменяем json
    with open(FILES_DIR / "0.json", "r", encoding="utf-8") as file:
        pattern = json.load(file)

    pattern["bean"]["pass"] = xui_id
    pattern["bean"]["name"] = f"{chat_id} PC"
    logger.debug("0.json отредактирован")

    # шифруем json
    encrypted_json = encrypt_json(pattern, aes_key)

    with open(dst / "config" / "profiles" / "0.json", "wb") as file:
        file.write(encrypted_json)
        # json.dump(pattern, file, ensure_ascii=False, indent=4)
    logger.debug("0.json зашифрован и сохранен")
    msg = msg[:-10] + "▮▮▯▯▯▯▯▯▯▯"
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=msg,
        parse_mode="HTML"
    )

    # создаём архив
    archive_path = FILES_DIR / "temp" / f"nekoray_archive_{user_id}_{randint}.zip"
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", dst)
    logger.debug("Архив создан")
    msg = msg[:-10] + "▮▮▮▮▯▯▯▯▯▯"
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=msg,
        parse_mode="HTML"
    )

    # возвращаем InputFile
    return [FSInputFile(str(archive_path)), FSInputFile(str(FILES_DIR / "nekoray_archive_dll.zip")), dst, archive_path]

async def get_link(user_id: str, platform: str | None="Android"):
    xui_data = xui.get_user_data(user_id)

    xui_id = xui_data[platform]["id"]
    xui_email = xui_data[platform]["email"].replace(" ", "%20")

    addr = "vless://"
    body = "@91.228.153.25:443?type=tcp&security=reality&pbk=NbVaXjLA9Q1w1lcBc3vmcDYkSyKbEc7LNbIC1FPK9SI&fp=chrome&sni=samsung.com&sid=&spx=%2F&flow=xtls-rprx-vision#VLESS%20Reality-"

    return addr + xui_id + body + xui_email


