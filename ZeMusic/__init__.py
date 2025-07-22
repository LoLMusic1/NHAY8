import asyncio
from ZeMusic.logging import LOGGER

# تهيئة ZeMusic Bot مع Telethon
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

# تهيئة مدير cookies
try:
    import asyncio
    from ZeMusic.core.cookies_manager import cookies_manager
    
    # تهيئة مدير cookies في background
    async def init_cookies():
        try:
            await cookies_manager.initialize()
            LOGGER(__name__).info("✅ تم تهيئة مدير Cookies بنجاح")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ تعذر تهيئة مدير Cookies: {e}")
    
    # تشغيل التهيئة
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # إذا كان هناك loop يعمل، استخدم task
            asyncio.create_task(init_cookies())
        else:
            # إذا لم يكن هناك loop، ستعمل لاحقاً
            pass
    except:
        # سيتم التهيئة عند أول استخدام
        pass
        
except Exception as e:
    LOGGER(__name__).warning(f"⚠️ تعذر تحميل مدير Cookies: {e}")

# تصدير app من طبقة التوافق
try:
    from ZeMusic.pyrogram_compatibility import app
    LOGGER(__name__).info("✅ تم تصدير app من Telethon")
except Exception as e:
    LOGGER(__name__).error(f"❌ خطأ في تصدير app: {e}")
    app = None

# تصدير المنصات للتوافق
try:
    from ZeMusic.platforms import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube
    LOGGER(__name__).info("✅ تم تصدير منصات الموسيقى")
except Exception as e:
    LOGGER(__name__).error(f"❌ خطأ في تصدير المنصات: {e}")

# تصدير الكربون (إذا كان موجود)
try:
    from ZeMusic.utils.thumbnails import Carbon
    LOGGER(__name__).info("✅ تم تصدير Carbon")
except Exception as e:
    # Carbon ليس ضروري للوظيفة الأساسية
    pass
