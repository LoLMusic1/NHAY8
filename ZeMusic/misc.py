import socket
import time

try:
    import heroku3
except ImportError:
    heroku3 = None
import config
from .logging import LOGGER

# قائمة السُوبر يوزرز (SUDOERS) - نظام بسيط مع Telethon
class TelethonSudoers:
    """نظام بسيط لإدارة المديرين مع Telethon"""
    def __init__(self):
        self._users = set()
    
    def add(self, user_id):
        if user_id:
            self._users.add(int(user_id))
    
    def __contains__(self, user_id):
        return int(user_id) in self._users
    
    def __len__(self):
        return len(self._users)
    
    def __iter__(self):
        return iter(self._users)

SUDOERS = TelethonSudoers()

HAPP = None
_boot_ = time.time()


def is_heroku():
    return "heroku" in socket.getfqdn()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "",
    "git",
    "heroku",
    "push",
    str(config.HEROKU_API_KEY),
    "https",
    str(config.HEROKU_APP_NAME),
    "HEAD",
    "master",
]


def dbb():
    """
    تهيئة قاعدة بيانات محلية (في الذاكرة) للمسارات المؤقتة.
    تم استبدالها بنظام SQLite الجديد.
    """
    global db
    db = {}
    LOGGER(__name__).info("Local Database Initialized.")

# تهيئة db للتوافق مع الكود القديم
db = {}


async def sudo():
    """
    تحميل قائمة sudoers من قاعدة البيانات الجديدة.
    """
    global SUDOERS
    # نظّف أي مكونات سابقة
    SUDOERS = filters.user()
    
    # أضف المعرفات الثابتة من config
    SUDOERS.add(config.OWNER_ID)
    SUDOERS.add(config.DAV)
    
    # تحميل المديرين من قاعدة البيانات
    try:
        from ZeMusic.core.database import db
        sudoers_list = await db.get_sudoers()
        for user_id in sudoers_list:
            SUDOERS.add(user_id)
        LOGGER(__name__).info(f"✅ تم تحميل {len(sudoers_list)} مدير من قاعدة البيانات SQLite")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في تحميل المديرين: {e}")
    
    LOGGER(__name__).info("✅ تم تحميل sudo(): استخدام قاعدة البيانات SQLite الجديدة")


def heroku():
    """
    تكوين تطبيق Heroku إذا كنا على بيئة Heroku.
    """
    global HAPP
    if is_heroku() and heroku3:
        if config.HEROKU_API_KEY and config.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(config.HEROKU_API_KEY)
                HAPP = Heroku.app(config.HEROKU_APP_NAME)
                LOGGER(__name__).info("تم تكوين تطبيق Heroku.")
            except BaseException:
                LOGGER(__name__).warning(
                    "Please make sure your Heroku API Key and App name are configured correctly."
                )
    elif is_heroku() and not heroku3:
        LOGGER(__name__).warning("heroku3 library not installed, Heroku features disabled.")
