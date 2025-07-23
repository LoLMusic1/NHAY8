import logging as python_logging

python_logging.basicConfig(
    level=python_logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        python_logging.StreamHandler(),  # فقط عرض السجلات في الطرفية
    ],
)

python_logging.getLogger("httpx").setLevel(python_logging.ERROR)
python_logging.getLogger("pymongo").setLevel(python_logging.ERROR)
python_logging.getLogger("pyrogram").setLevel(python_logging.ERROR)
python_logging.getLogger("pytgcalls").setLevel(python_logging.ERROR)
python_logging.getLogger("telethon").setLevel(python_logging.WARNING)  # تقليل سجلات Telethon


def LOGGER(name: str) -> python_logging.Logger:
    return python_logging.getLogger(name)
