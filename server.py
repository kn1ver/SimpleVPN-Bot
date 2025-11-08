from quart import Quart, request, jsonify, send_file
import base64, os, glob, json, shutil, random, hashlib, asyncio
import utils.xui as xui
import utils.sqlite as db
from utils.logger import set_logger
from utils.utils import encrypt_json

app = Quart(__name__)
logger = set_logger("logs/server.log", True)

@app.route('/api/create_archives', methods=['POST'])
async def create_archives():
    """
    Создаёт уникальный архив пользователя.
    Ожидает JSON: {"chat_id": "<уникальный chat_id пользователя>"}
    """

    data = await request.get_json()
    if not data or "chat_id" not in data:
        return jsonify({"success": False, "error": "Missing chat_id"}), 400

    try:
        user_id = str(data["chat_id"]).strip()
        base_dir = os.path.join("files")
        personal_archive_dir = os.path.join(base_dir, "temp")

        # создаём temp-папку, если нет
        os.makedirs(personal_archive_dir, exist_ok=True)

        # получаем данные XUI и формируем ключ
        xui_data = xui.get_user_data(user_id)
        xui_id = xui_data["PC"]["id"]
        aes_key = hashlib.sha256(str(xui_id).encode("utf-8")).digest()
        randint = random.randint(0, 999)

        # копируем базовую папку nekoray
        src = os.path.join(base_dir, "nekoray")
        dst = os.path.join(personal_archive_dir, f"nekoray_{user_id}_{randint}")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.debug(f"create_archives | {user_id}: Папка nekoray скопирована")

        # читаем шаблон config 0.json
        src_json = os.path.join(src, "config", "profiles", "0.json")
        with open(src_json, "r", encoding="utf-8") as file:
            pattern = json.load(file)

        # изменяем параметры
        pattern["bean"]["pass"] = xui_id
        pattern["bean"]["name"] = f"{user_id} PC"
        logger.debug(f"create_archives | {user_id}: 0.json отредактирован")

        # шифруем json
        encrypted_json = encrypt_json(pattern, aes_key)

        dst_json = os.path.join(dst, "config", "profiles", "0.json")
        os.makedirs(os.path.dirname(dst_json), exist_ok=True)
        with open(dst_json, "wb") as file:
            file.write(encrypted_json)

        logger.debug(f"create_archives | {user_id}: 0.json зашифрован и сохранён")

        # создаём архив
        archive_name = f"nekoray_archive_{user_id}_{randint}.zip"
        archive_path = os.path.join(personal_archive_dir, archive_name)
        shutil.make_archive(archive_path[:-4], "zip", dst)
        logger.debug(f"create_archives | {user_id}: Архив создан {archive_name}")

        return jsonify({"success": True, "archive": archive_name})

    except Exception as e:
        logger.exception("Ошибка в create_archives")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/delete_archives', methods=['POST'])
async def delete_archives():
    """
    Удаляет все временные архивы и рабочие папки пользователя.
    Ожидает JSON: {"chat_id": "<уникальный chat_id пользователя>"}
    """
    import os, glob, shutil

    data = await request.get_json()
    if not data or "chat_id" not in data:
        return jsonify({"success": False, "error": "Missing chat_id"}), 400

    chat_id = str(data["chat_id"]).strip()
    base_path = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_path, "files", "temp")

    try:
        if not os.path.exists(temp_dir):
            return jsonify({"success": False, "error": "Temp folder not found"}), 404

        # Маска для архивов и папок
        archive_pattern = os.path.join(temp_dir, f"nekoray_archive_{chat_id}_*.zip")
        folder_pattern = os.path.join(temp_dir, f"nekoray_{chat_id}_*")

        # Находим все совпадения
        archives = glob.glob(archive_pattern)
        folders = glob.glob(folder_pattern)

        deleted_count = 0

        # Удаляем архивы
        for path in archives:
            try:
                os.remove(path)
                deleted_count += 1
                logger.debug(f"delete_archives | {chat_id}: Удалён архив {os.path.basename(path)}")
            except Exception as e:
                logger.warning(f"delete_archives | Ошибка при удалении {path}: {e}")

        # Удаляем временные папки
        for path in folders:
            try:
                shutil.rmtree(path, ignore_errors=True)
                deleted_count += 1
                logger.debug(f"delete_archives | {chat_id}: Удалена папка {os.path.basename(path)}")
            except Exception as e:
                logger.warning(f"delete_archives | Ошибка при удалении {path}: {e}")

        if deleted_count == 0:
            return jsonify({"success": False, "error": f"No archives found for chat_id={chat_id}"}), 404

        logger.info(f"delete_archives | {chat_id}: Удалено {deleted_count} элементов")
        return jsonify({"success": True, "deleted": deleted_count})

    except Exception as e:
        logger.exception("Ошибка при удалении архивов")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get_archives', methods=['POST'])
async def get_archives():
    """
    Отправляет два архива как единый zip-пакет.
    Ожидает JSON: {"chat_id": "<id пользователя>"}
    """
    import io, zipfile, glob, os

    data = await request.get_json()
    if not data or "chat_id" not in data:
        return jsonify({"success": False, "error": "Missing chat_id"}), 400

    chat_id = str(data["chat_id"]).strip()
    personal_arch_dir = os.path.join("files", "temp")
    base_dir = os.path.join("files")

    try:
        # ищем архив пользователя
        pattern = os.path.join(personal_arch_dir, f"nekoray_archive_{chat_id}_*.zip")
        matches = glob.glob(pattern)
        if not matches:
            return jsonify({"success": False, "error": f"No archive for chat_id={chat_id}"}), 404
        user_archive = max(matches, key=os.path.getmtime)

        # фиксированный dll-архив
        dll_archive = os.path.join(base_dir, "nekoray_archive_dll.zip")
        if not os.path.exists(dll_archive):
            return jsonify({"success": False, "error": "DLL archive not found"}), 404

        # упаковываем оба архива во временный zip в памяти
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(user_archive, os.path.basename(user_archive))
            zf.write(dll_archive, os.path.basename(dll_archive))
        buf.seek(0)

        logger.info(f"[get_archives] chat_id={chat_id}: отправляем оба архива")

        # потоковая отдача — без блокировки event loop
        return await send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"archives_{chat_id}.zip"
        )
    except Exception as e:
        logger.exception("Ошибка при формировании архивов")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/check_key', methods=['POST'])
async def check_key():
    """
    Проверка ключа доступа.
    Ожидает JSON: {"xui_id": "xui_id пользователя"}
    """
    data = await request.get_json()
    if not data or 'xui_id' not in data:
        return jsonify({"error": "Отсутствует поле 'xui_id'"}), 400

    xui_id = data['xui_id']
    try:
        user_data = await db.get_user_data("xui_id", xui_id, ["activated", "chat_id"])
        if user_data:
            activated = user_data[0][0]
            chat_id = user_data[0][1]
            logger.debug(f"[check_key] {activated} {chat_id}")
        else:
            activated = ""
            chat_id = ""

        return jsonify({"success": True, "activated": activated, "chat_id": chat_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/set_activate', methods=['POST'])
async def set_activate():
    data = await request.get_json()
    if not data or 'chat_id' not in data:
        return jsonify({"error": "Отсутствует поле 'chat_id'"}), 400

    chat_id = data['chat_id']
    logger.debug(f"[set_activate] {chat_id}")
    try:
        await db.set_user_data('chat_id', str(chat_id), 'activated', '1')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
async def health():
    return jsonify({
        "status": "healthy",
        "functions_count": 2,
        "async_support": True
    })

# ------------------------------
# Запуск сервера
# ------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5018, debug=True)
