from quart import Quart, request, jsonify
import asyncio
import utils.sqlite as db  # ваш модуль для работы с базой

app = Quart(__name__)

# ------------------------------
# Функция проверки ключа
# ------------------------------
@app.route('/api/check_key', methods=['POST'])
async def check_key():
    """
    Проверка ключа доступа.
    Ожидает JSON: {"access_key": "ключ_доступа"}
    """
    data = await request.get_json()
    if not data or 'access_key' not in data:
        return jsonify({"error": "Отсутствует поле 'access_key'"}), 400

    access_key = data['access_key']
    try:
        user_data = await db.search_for_key(access_key)
        activated = user_data[1]
        chat_id = user_data[0]
        await db.set_user_data('chat_id', chat_id, 'activated', '1')
        logger.debug(f"{user_data}")
        return jsonify({"success": True, "activated": activated[0], "chat_id": chat_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/set_activated', methods=['POST'])
async def check_key():
    data = await request.get_json()
    if not data or 'chat_id' not in data:
        return jsonify({"error": "Отсутствует поле 'chat_id'"}), 400

    chat_id = data['chat_id']
    try:
        await db.set_user_data('chat_id', chat_id, 'activated', '1')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ------------------------------
# Функция health check
# ------------------------------
@app.route('/api/health', methods=['GET'])
async def health():
    return jsonify({
        "status": "healthy",
        "functions_count": 1,  # только check_key
        "async_support": True
    })

# ------------------------------
# Запуск сервера
# ------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
