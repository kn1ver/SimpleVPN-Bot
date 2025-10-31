try:
    import os
    import sys
    import platform
    import json
    import zipfile
    import subprocess
    import hashlib
    import requests
    import traceback
    from logger import set_logger

    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    def get_base_path():
        """
        Возвращает папку, откуда запускается приложение.
        - если приложение "заморожено" (pyinstaller/py2exe), возвращаем папку exe (sys.executable)
        - иначе — папку, где лежит текущий .py (как раньше)
        """
        # PyInstaller (and similar) sets an attribute 'frozen' on sys and uses sys.executable
        if getattr(sys, "frozen", False):
            # Когда используется --onefile, исполняемый файл распакован во временную папку,
            # но сами внешние файлы (архивы) обычно лежат рядом с exe, поэтому берём dirname(sys.executable)
            return os.path.dirname(sys.executable)
        # fallback for regular python execution
        return os.path.dirname(os.path.abspath(file))

    # ----------- Настройки -----------
    APP_NAME = "SimpleVPN"
    BASE_PATH = get_base_path()

    DEST_FOLDER_NAME = "SimpleVPN"
    DEST_FOLDER = os.path.join(BASE_PATH, DEST_FOLDER_NAME)

    API_URL = "http://91.228.153.25:5018"
    EXE_FILE = os.path.join(DEST_FOLDER, "nekobox.exe")
    ENCRYPTED_FILE = os.path.join(DEST_FOLDER, "config", "profiles", "0.json")
    DECRYPTED_FILE = os.path.join(DEST_FOLDER, "config", "profiles", "0.json")

    logger = set_logger("logs/launcher.log", False)

    #--------------- работа с API ---------------------
    def check_activation_key(user_xui_id):
        json_data = {"xui_id": str(user_xui_id)}
        try:
            response = requests.post(f"{API_URL}/api/check_key", json=json_data, timeout=10)
            response.raise_for_status()
            logger.debug(response.json())
            return response.json()
        except Exception as e:
            logger.exception("Ошибка запроса check_activation_key")
            return {"success": False, "error": str(e)}

    def set_activated(chat_id):
        json_data = {"chat_id": chat_id}
        try:
            response = requests.post(f"{API_URL}/api/set_activate", json=json_data, timeout=10)
            response.raise_for_status()
            logger.debug(response.json())
        except Exception:
            logger.exception("Ошибка set_activated")

        return


    # -------------- работа с файлами -----------------
    def extract_archives():
        """
        Ищет и распаковывает архивы nekoray_archive*.zip в папку DEST_FOLDER,
        где DEST_FOLDER формируется относительно текущего базового пути.
        """
        base_path = get_base_path()
        logger.info(f"Ищем архивы в папке запуска: {base_path}")

        # Создадим локальную переменную dest_folder, чтобы распаковка шла рядом с exe/.py
        dest_folder = os.path.join(base_path, DEST_FOLDER_NAME)
        found = False

        try:
            entries = os.listdir(base_path)
        except Exception as e:
            logger.error(f"Не удалось прочитать содержимое папки {base_path}: {e}")
            return

        for fname in entries:
            # проверяем только файлы в каталоге запуска
            if "nekoray_archive" in fname and fname.endswith(".zip"):
                found = True
                archive_path = os.path.join(base_path, fname)
                logger.info(f"Нашёл архив: {archive_path}")
                try:
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        # распаковываем в абсолютную папку dest_folder
                        os.makedirs(dest_folder, exist_ok=True)
                        zip_ref.extractall(dest_folder)
                        logger.info(f"Распаковал {fname} -> {dest_folder}")
                except zipfile.BadZipFile:
                    logger.error(f"Файл {archive_path} не является zip-архивом или повреждён.")
                except Exception as e:
                    logger.error(f"Ошибка при распаковке {archive_path}: {e}")

        if not found:
            logger.warning("Не найдено файлов nekoray_archive*.zip в папке запуска.")
        else:
            # полезное визуальное подтверждение для пользователя (как было)
            print("Архивы успешно обработаны.")

    def decrypt_json(encrypted_data: bytes, aes_key: bytes) -> dict:
        """Расшифровывает бинарные данные обратно в JSON"""
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return json.loads(plaintext.decode("utf-8"))

    def save_decrypted_file(key: str):
        """Дешифруем ENCRYPTED_FILE -> DECRYPTED_FILE. Выдаёт понятную ошибку, если не найден."""
        # пересоздаём абсолютные пути на момент вызова (на случай, если BASE_PATH изменится)
        enc = ENCRYPTED_FILE
        dec = DECRYPTED_FILE

        logger.info(f"Ожидаем зашифрованный файл по пути: {enc}")
        if not os.path.exists(enc):
            # диагностическое сообщение: перечислим ближайшие файлы для отладки
            parent = os.path.dirname(enc)
            logger.error(f"Зашифрованный файл не найден: {enc}")
            raise FileNotFoundError(f"Encrypted file not found: {enc}")

        # готовим ключ и читаем
        bytes_key = hashlib.sha256(str(key).encode("utf-8")).digest()
        with open(enc, "rb") as f:
            encrypted_data = f.read()

        decrypted_json = decrypt_json(encrypted_data, bytes_key)

        # сохраняем в тот же путь (или можно указать отдельный)
        os.makedirs(os.path.dirname(dec), exist_ok=True)
        with open(dec, "w", encoding="utf-8") as f:
            json.dump(decrypted_json, f, ensure_ascii=False, indent=2)
        logger.info(f"Файл {enc} успешно дешифрован и сохранён как {dec}.")


    #--------------- файл-маркер -----------------------
    def get_marker_path(app_name: str):
        system = platform.system()
        if system == "Windows":
            base_dir = os.environ.get("ProgramData", r"C:\ProgramData")
        else:
            base_dir = "/var/lib"
        path = os.path.join(base_dir, app_name)
        try:
            os.makedirs(path, exist_ok=True)
        except PermissionError:
            home_fallback = os.path.expanduser(f"~/.local/share/{app_name}")
            os.makedirs(home_fallback, exist_ok=True)
            path = home_fallback
        return os.path.join(path, "activated")

    def create_activation_marker(xui_id, app_name: str):
        marker_path = get_marker_path(app_name)
        try:
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write(xui_id.strip())
            logger.info(f"Маркер создан: {marker_path}")
        except Exception as e:
            logger.error(f"Не удалось создать маркер: {e}")

    def read_activation_marker(app_name: str):
        """Возвращает xui_id из файла активации"""
        marker_path = get_marker_path(app_name)
        if not os.path.exists(marker_path):
            logger.info("Файл активации не найден.")
            return None

        try:
            with open(marker_path, "r", encoding="utf-8") as f:
                xui_id = f.read().strip()
            if xui_id:
                logger.info(f"Найден xui_id: {xui_id}")
                return xui_id
            else:
                logger.warning("Файл активации пуст.")
                return None
        except Exception as e:
            logger.error(f"Ошибка чтения файла активации: {e}")
            return None


    #--------------- main-функции ----------------------
    def run_exe():
        if not os.path.exists(EXE_FILE):
            logger.error(f"exe не найден: {EXE_FILE}")
            return
        print(f"Запуск {EXE_FILE}...")
        subprocess.run([EXE_FILE], check=True)

    def build(xui_id):
        extract_archives()
        save_decrypted_file(xui_id)
        run_exe()
        print(f"В дальнейшем вы можете запускать VPN через файл {EXE_FILE}.")
        input("Для выхода нажмите любую клавишу...")
        return

    def main():
        xui_id = input("Введите ключ активации: ").strip()
        resp = check_activation_key(xui_id)

        if not resp.get('success', False):
            print("Ошибка сервера, попробуйте позже.")
            input("Для выхода нажмите любую клавишу...")
            return

        if resp.get('activated') == 1:
            print("Ключ уже активирован.")
            input("Для выхода нажмите любую клавишу...")
            return

        if not resp.get('chat_id'):
            print("Неверный ключ.")
            input("Для выхода нажмите любую клавишу...")
            return

        print("Ключ принят.")
        set_activated(resp['chat_id'])
        create_activation_marker(xui_id, APP_NAME)
        build(xui_id)
        return


    if __name__ == "__main__":
        try:
            xui_id = read_activation_marker(APP_NAME)

            if xui_id:
                build(xui_id)
            else:
                main()
        except Exception as e:
            print(f"Ошибка: {e}")
            traceback.print_exc()
            input()
except Exception as e:
    print(f"Ошибка: {e}")
    traceback.print_exc()
    input()
