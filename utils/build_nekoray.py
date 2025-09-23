import os
import json
import zipfile
import subprocess
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ----------- Настройки -----------
API_URL = "https://example.com/validate_key"  # позже заменить на реальный URL
DEST_FOLDER = "app_folder"
ENCRYPTED_FILE = os.path.join(DEST_FOLDER, "config", "profiles", "0.json")
DECRYPTED_FILE = os.path.join(DEST_FOLDER, "config", "profiles", "0.json")
EXE_FILE = os.path.join(DEST_FOLDER, "nekobox.exe")
# ---------------------------------

def check_activation_key():
    """
    Заглушка для проверки ключа.
    Реально здесь будет requests.post(API_URL, json={"key": key})
    """
    # Пример запроса:
    # response = requests.post(API_URL, json={"key": key})
    # return response.json().get("valid", False)
    return True

def extract_archives():
    for file in os.listdir("."):  # "." = текущая папка рядом с exe
        if "nekoray_archive" in file and file.endswith(".zip"):
            print(f"Нашёл архив: {file}")
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(DEST_FOLDER)
    print("Архивы успешно распакованы.")

def decrypt_json(encrypted_data: bytes, key: bytes) -> dict:
    """Расшифровывает бинарные данные обратно в JSON"""
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

    return json.loads(plaintext.decode("utf-8"))

def save_decrypted_file(key: str):
    bytes_key = hashlib.sha256(str(key).encode("utf-8")).digest()
    with open(ENCRYPTED_FILE, "rb") as f:
        encrypted_data = f.read()

    decrypted_json = decrypt_json(encrypted_data, bytes_key)
    with open(DECRYPTED_FILE, "w") as f:
        json.dump(decrypted_json, f, ensure_ascii=False, indent=2)
    print(f"Файл {ENCRYPTED_FILE} успешно дешифрован и сохранён.")

def run_exe():
    print(f"Запуск {EXE_FILE}...")
    subprocess.run(EXE_FILE, check=True)

def main():
    key = input("Введите ключ активации: ").strip()
    if not check_activation_key():
        print("Неверный ключ.")
        input("Для выхода нажмите любую клавишу...")
        return

    print("Ключ принят.")
    extract_archives()
    save_decrypted_file(key)
    run_exe()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ошибка: {e}")
        input()
