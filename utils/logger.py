import logging
import sys
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL

        # Сохраняем оригинальные значения
        original_levelname = record.levelname
        original_msg = record.getMessage()

        # Красим только для консоли
        record.levelname = f"{level_color}{original_levelname}{reset}"
        record.msg = f"{level_color}{original_msg}{reset}"

        formatted = super().format(record)

        # Возвращаем оригинал, чтобы file_handler получил чистый текст
        record.levelname = original_levelname
        record.msg = original_msg

        return formatted


# Формат логов
FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"

# Настраиваем логгер
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)

# Консольный хендлер (с цветами)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter(FORMAT, DATE_FORMAT))

# Файловый хендлер с ротацией (без цветов)
file_handler = RotatingFileHandler(
    "bot.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(FORMAT, DATE_FORMAT))

# Добавляем оба хендлера
logger.addHandler(console_handler)
logger.addHandler(file_handler)
