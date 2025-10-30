import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("PROD_BOT_TOKEN")

XUI_URL = os.getenv("XUI_URL")
XUI_LOGIN = os.getenv("XUI_LOGIN")
XUI_PASS = os.getenv("XUI_PASS")
