import requests
import json
import time
import uuid
import utils.utils as utils
from utils.logger import logger

from config import XUI_LOGIN, XUI_PASS, XUI_URL

session = requests.Session()
INBOUND_ID = 1

def xui_login():
    r = session.post(f"{XUI_URL}/login", json={
        "username": XUI_LOGIN,
        "password": XUI_PASS
    })
    if r.status_code != 200:
        raise Exception("Login failed")

    return r

def get_user_data(user_id: str):
    """
    Возвращает email, активность, статус соединения, трафик (загрузка/скачивание/всего) и дату окончания by user email
    """
    xui_login()
    result = {}

    r = session.get(f"{XUI_URL}/xui/API/inbounds/")
    r.raise_for_status()
    all_inbounds = r.json()
    all_inbounds["obj"][0]["settings"] = json.loads(all_inbounds["obj"][0]["settings"])

    r = session.post(f"{XUI_URL}/xui/API/inbounds/onlines")
    r.raise_for_status()
    onlines = r.json()

    logger.debug(f"get_usr_data | onlines:\n{onlines}")

    for client in all_inbounds["obj"][0]["clientStats"]:
        email = client["email"].split(" ")
        if email[0] == user_id:

            if f"{user_id} {email[1]}" in onlines["obj"]:
                client["online"] = True
            else:
                client["online"] = False

            client["up"] = utils.size_parser(client["up"])
            client["down"] = utils.size_parser(client["down"])
            client["expiryTime"] = utils.parse_expiry_time(client["expiryTime"])

            result[email[1]] = client

    for client in all_inbounds["obj"][0]["settings"]["clients"]:
        email = client["email"].split(" ")
        if email[0] == user_id:
            if email[1] == "PC":
                result["PC"]["id"] = client["id"]
                result["PC"]["subId"] = client["subId"]

            elif email[1] == "Android":
                result["Android"]["id"] = client["id"]
                result["Android"]["subId"] = client["subId"]

            elif email[1] == "IOS":
                result["IOS"]["id"] = client["id"]
                result["IOS"]["subId"] = client["subId"]

    # with open("test_inbounds.json", "w") as f:
    #     json.dump(all_inbounds, f)

    # with open("test_client.json", "w") as f:
    #     json.dump(result, f)

    return result

def reg_user_connection(user_id: str, expiry_time: int):

    xui_login()

    platforms = ["PC", "Android", "IOS"]

    for platform in platforms:
        client_uuid = str(uuid.uuid4())
        client_settings = {
            "clients": [{
                "id": client_uuid,
                "flow": "xtls-rprx-vision",
                "email": f"{user_id} {platform}",
                "totalGB": 0,
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": user_id,
                "subId": "autogen-" + client_uuid[:8],
                "limitIp": 1,
                "reset": 0
            }]
        }
        json_body = {
            "id": INBOUND_ID,
            "settings": json.dumps(client_settings)
        }
        r = session.post(f"{XUI_URL}/xui/API/inbounds/addClient/", json=json_body)
        logger.debug(f"reg_user_conn | Ответ сервера: {r.status_code} {r.text}")

    return True

def update_client_expiry(inbound_id: int, chat_id: str, new_expiry_days: int, logger=None):
    """
    Обновляет expiryTime пользователя в x-ui панели
    :param inbound_id: ID инбаунда
    :param chat_id: chat_id клиента из бота
    :param new_expiry_days: через сколько дней истекает подписка
    """
    xui_login()

    # Получаем inbound по ID
    r = session.get(f"{XUI_URL}/xui/API/inbounds/get/{inbound_id}")
    r.raise_for_status()
    inbound_data = r.json()

    if not inbound_data.get("success"):
        raise Exception(f"Не удалось получить inbound {inbound_id}: {r.text}")

    settings = json.loads(inbound_data["obj"]["settings"])
    clients = settings.get("clients", [])
    platforms = ["PC", "Android", "IOS"]

    # Ищем нужного клиента
    for platform in platforms:
        target = None
        for c in clients:
            if c.get("email") == f"{chat_id} {platform}":
                target = c
                break

        if not target:
            raise Exception(f"❌ Клиент с email '{chat_id}' не найден в inbound {inbound_id}")

        # Обновляем дату истечения
        new_expiry_time = (int(time.time()) + new_expiry_days * 24 * 3600) * 1000
        target["expiryTime"] = new_expiry_time

        # Формируем JSON для обновления
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [target]
            }) # XUI ждёт объект клиента, не весь inbound
        }

        try:
            logger.debug(f"updt_clnt_expiry | json:\n{payload}")
        except Exception as e:
            pass

        client_id = target["id"]
        r = session.post(f"{XUI_URL}/xui/API/inbounds/updateClient/{client_id}", json=payload)
        r.raise_for_status()

        if r.status_code == 200:
            if logger:
                logger.debug(f"updt_clnt_expiry | обновлён expiryTime клиента '{chat_id} {platform}': {time.ctime(new_expiry_time/1000)}")
            else:
                print(f"updt_clnt_expiry | обновлён expiryTime клиента '{chat_id} {platform}': {time.ctime(new_expiry_time/1000)}")
        else:
            if logger:
                logger.error(f"updt_clnt_expiry | Ошибка обновления expiryTime: {r.text}")
            else:
                print(f"updt_clnt_expiry | Ошибка обновления expiryTime: {r.text}")

    return True
