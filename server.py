from quart import Quart, request, jsonify
import asyncio
import utils.sqlite as db
from utils.logger import logger

app = Quart(__name__)

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
    app.run(host="127.0.0.1", port=5018, debug=True)
