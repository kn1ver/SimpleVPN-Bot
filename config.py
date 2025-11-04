import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TEST_BOT_TOKEN")

XUI_URL = os.getenv("XUI_URL")
XUI_LOGIN = os.getenv("XUI_LOGIN")
XUI_PASS = os.getenv("XUI_PASS")

MESSAGES = {
    "main_menu":"🚀 Добро пожаловать в SimpleVPN!\nБезопасный и быстрый интернет без отслеживания и скрытых списаний",
    "paid_0":   "Похоже, Вы еще не подключены к нашему VPN или не оплатили текущий период",

    # --------- PROFILE ---------
    "profile_platform": (
                "<b>   {platform}\n</b>"
                "💡Активен: {enable}\n"
                "🌐 Статус соединения: {online}\n"
                "🔼 Загрузка: {up}\n🔽 Скачивание: {down}\n"
                "📅 Окончание: {expiry}\n\n"
    ),

    # --------- PLATFORMS ---------
    "platforms":"На какую платформу Вы хотите установить VPN?",
    "platforms_pc": (
                "С порядоком установки VPN на компьютер вы можете ознакомиться по этой ссылке:\n"
                "https://teletype.in/@kn1ver/install-pc \n\n"
                "<b>Ваш ключ активации</b>: <code>{xui_id}</code>\n\n Архивы отправляются ▯▯▯▯▯▯▯▯▯▯"
    ),
    "platforms_adnroid": (
                "Порядок установки VPN на android:\n\n"
                "  1. Откройте ссылку: https://drive.google.com/file/d/1MsrZp13yQUGQHRZIAJHYU6CdSQIwffel/view?usp=sharing \n"
                "  2. Загрузите файл <u>v2rayNG_1.10.23.apk</u> с диска\n"
                "  3. Откройте этот файл и установите приложение\n"
                "  4. Следуйте инструкциям отсюда: https://teletype.in/@kn1ver/Android-install \n\n"
                "Ресурсы:\n"
                "<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                "<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>"
    ),
    "platforms_ios": (
                "Для установки настройки VPN\nСледуйте инструкциям отсюда: https://teletype.in/@kn1ver/install-ios \n\n"
                "Ресурсы:\n"
                "<u>Конфиг</u>:\n <code>{user_config}</code>\n\n"
                "<u>Правила маршрутизации</u>:\n <code>{routing_rules}</code>"
    ),

    # --------- PAYMENT ---------
    "pay_conditions": (
                "🌐 После оплаты вы получаете полный доступ к <b>SimpleVPN</b>.\n"
                "Установить его можно на <b>Android, ПК и iOS</b> — по одному устройству для каждой платформы.\n\n"
                "💳 Стоимость подписки всего <i><b>200</b>руб за <b>31</b> день</i>\n"
                "Мы честно напомним о платеже за <b>7 и 3 дня</b>, чтобы вы успели решить, остаёмся ли вместе дальше.\n"
                "✨ Никаких скрытых списаний"
    ),
    "pay_details": (
                "Для оплаты подписки переведите деньги по следующим реквизитам:\n\n"

                "    Номер карты: <code>2200700893574078</code>\n"
                "    Номер телефона: <code>89397136806</code>\n"
                "    Банк: ТБанк\n\n"

                "    Сумма: 200 рублей\n\n"

                "После оплаты отправьте скриншот о переводе в этот чат."
    ),

    # --------- SUPPORT ---------
    "help": (
                "Как можно подробнее опишите проблему, с которой вы столкнулись, в ответном сообщении. Мы постараемся помочь вам как можно быстрее.\n"
                "(Вы можете приложить до 1 фотографии/файла)"
    ),
    "problem_accepted": (
                "Сообщение доставлено. В скором времени с вами свяжится поддержка.\nВы можете дополнить обращение, отправив детали сюда же"
    ),

    # --------- SUBSCRIBLE ---------
    "payment_approved": (
                "Оплата подписки была подтверждена"
    ),
    "payment_deny": (
                'Оплата подписки была отклонена. Вы можете спросить о причинах в разделе "Поддрежка"'
    ),

    "sub_renewed": (
                "Подписка продлена. Спасибо за покупку!\n"
                "Истекает: {expires_at}\n"
    ),
    "sub_connected": (
                "Подписка подключена. Спасибо за покупку!\n"
                "Истекает: {expires_at}\n"
                'Перейдите в раздел "Установить VPN" для установки.'
    ),
    "sub_already_connected": (
                "У вас уже есть действующая подписка\nПродлить её будет можно за 7 дней до окончания текущего периода"
    ),

    # --------- SCREENSHOT ---------
    "without_photo": (
                "В сообщении не обнаружено фото\nДля подтверждения оплаты отправьте скриншот из банка"
    ),
    "found_scrnShot": (
                "Подписка будет оплачена, когда администратор подтвердит перевод. Вы будете оповещены\nСпасибо, что выбрали SimpleVPN"
    )
}
ROUTING_RULES = {
    "adnroid": '[{"enabled":true,"ip":["geoip:ru"],"looked":false,"outboundTag":"direct","remarks":"geoip direct"},{"domain":["geosite:category-gov-ru","geosite:yandex","geosite:vk","regexp:xn--"],"enabled":true,"looked":false,"outboundTag":"direct","remarks":"geosite direct"},{"domain":["geosite:category-ads-all"],"enabled":true,"looked":false,"outboundTag":"block","remarks":"ads block"},{"enabled":true,"ip":["geoip:private"],"looked":false,"outboundTag":"direct","remarks":"geoip private"},{"domain":["geosite:private"],"enabled":true,"looked":false,"outboundTag":"direct","remarks":"geosite private"}]',
    "ios": 'v2box://routes?multi=W3siZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cnUiXSwibG9ja2VkIjpmYWxzZSwib3V0Ym91bmRUYWciOiJkaXJlY3QiLCJyZW1hcmtzIjoiZ2VvaXAgZGlyZWN0In0seyJkb21haW4iOlsiZ2Vvc2l0ZTpjYXRlZ29yeS1nb3YtcnUiLCJnZW9zaXRlOnlhbmRleCIsImdlb3NpdGU6dmsiLCJyZWdleHA6eG4tLSJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9zaXRlIGRpcmVjdCJ9LHsiZG9tYWluIjpbImdlb3NpdGU6Y2F0ZWdvcnktYWRzLWFsbCJdLCJlbmFibGVkIjp0cnVlLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImJsb2NrIiwicmVtYXJrcyI6ImFkcyBibG9jayJ9LHsiZW5hYmxlZCI6dHJ1ZSwiaXAiOlsiZ2VvaXA6cHJpdmF0ZSJdLCJsb2NrZWQiOmZhbHNlLCJvdXRib3VuZFRhZyI6ImRpcmVjdCIsInJlbWFya3MiOiJnZW9pcCBwcml2YXRlIn0seyJkb21haW4iOlsiZ2Vvc2l0ZTpwcml2YXRlIl0sImVuYWJsZWQiOnRydWUsImxvY2tlZCI6ZmFsc2UsIm91dGJvdW5kVGFnIjoiZGlyZWN0IiwicmVtYXJrcyI6Imdlb3NpdGUgcHJpdmF0ZSJ9XQ=='
}
LINK_BODY = (
    "@91.228.153.25:443?type=tcp&security=reality&pbk=NbVaXjLA9Q1w1lcBc3vmcDYkSyKbEc7LNbIC1FPK9SI&fp=chrome&sni=samsung.com&sid=&spx=%2F&flow=xtls-rprx-vision#VLESS%20Reality-"
)


