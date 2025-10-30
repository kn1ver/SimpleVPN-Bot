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

    logger.debug(f"onlines: {onlines}")

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

def reg_user_connection(user_id: str):

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
                "expiryTime": int((time.time() + 31 * 24 * 3600) * 1000),
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
        logger.debug(f"Ответ сервера [addClient]: {r.status_code} {r.text}")

    return True

