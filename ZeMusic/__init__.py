import asyncio
from ZeMusic.logging import LOGGER

# استخدام Telethon بدلاً من TDLib
LOGGER(__name__).info("🔥 تهيئة ZeMusic مع Telethon")
LOGGER(__name__).info("🚀 Powered by Telethon v1.36.0")

# تهيئة مدير Telethon
try:
    from ZeMusic.core.telethon_client import telethon_manager
    LOGGER(__name__).info("✅ تم تحميل مدير Telethon بنجاح")
except Exception as e:
    LOGGER(__name__).error(f"❌ خطأ في تحميل مدير Telethon: {e}")

# تهيئة قاعدة البيانات
try:
    from ZeMusic.core.database import db
    LOGGER(__name__).info("✅ تم تحميل قاعدة البيانات بنجاح")
except Exception as e:
    LOGGER(__name__).error(f"❌ خطأ في تحميل قاعدة البيانات: {e}")

# تهيئة معالج الأوامر
try:
    from ZeMusic.core.command_handler import telethon_command_handler
    LOGGER(__name__).info("✅ تم تحميل معالج أوامر Telethon بنجاح")
except Exception as e:
    LOGGER(__name__).error(f"❌ خطأ في تحميل معالج الأوامر: {e}")

LOGGER(__name__).info("🎵 ZeMusic جاهز للانطلاق مع Telethon!")
