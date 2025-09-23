import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

XUI_URL = os.getenv("XUI_URL")
XUI_LOGIN = os.getenv("XUI_LOGIN")
XUI_PASS = os.getenv("XUI_PASS")

MESSAGES = {
    "start": "Добро пожаловать в бота для игры в Бункер!\nУдачной игры!",
    "main_room_msg": "title\n\nID Комнаты: room_id\nPIN-код: pin\nАдмин: admin\n\nСписок игроков:\nplayers\n\nОжидаем начала игры",
    "wait_room_data": "Введите ID комнаты, в которую хотите войти.\n\nЕсли вы входите в приватную комнату, укажите пин через двоеточие\nПример: 1001:9118",
}
