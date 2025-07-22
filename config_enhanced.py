#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot - Enhanced Configuration System
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Telethon Enhanced Edition

إعدادات متقدمة ومحسنة لبوت الموسيقى
مصممة للعمل مع 7000 مجموعة و 70000 مستخدم
"""

import re
import os
import json
import logging
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path

# تحميل متغيرات البيئة
try:
    from dotenv import load_dotenv
    load_dotenv()
    ENVIRONMENT_LOADED = True
except ImportError:
    ENVIRONMENT_LOADED = False
    print("⚠️ python-dotenv غير مثبت - سيتم استخدام متغيرات النظام فقط")

# ============================================
# إعدادات النظام الأساسية
# ============================================

@dataclass
class SystemConfig:
    """إعدادات النظام الأساسية"""
    
    # معلومات Telegram API
    api_id: int = int(os.getenv("API_ID", "20036317"))
    api_hash: str = os.getenv("API_HASH", "986cb4ba434870a62fe96da3b5f6d411")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    
    # معلومات البوت
    bot_name: str = os.getenv("BOT_NAME", "ZeMusic")
    bot_username: str = os.getenv("BOT_USERNAME", "")
    bot_id: Optional[int] = None
    
    # معلومات المالك
    owner_id: int = int(os.getenv("OWNER_ID", "7345311113"))
    owner_username: str = os.getenv("OWNER_USERNAME", "")
    
    # إعدادات الجهاز (للتخفي)
    device_model: str = os.getenv("DEVICE_MODEL", "ZeMusic Server")
    system_version: str = os.getenv("SYSTEM_VERSION", "Ubuntu 22.04 LTS")
    app_version: str = os.getenv("APP_VERSION", "3.0.0")
    
    # اللغة الافتراضية
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "ar")
    
    def __post_init__(self):
        """التحقق من صحة الإعدادات الأساسية"""
        if not self.bot_token:
            raise ValueError("❌ BOT_TOKEN مطلوب! احصل عليه من @BotFather")
        
        if self.api_id == 0:
            raise ValueError("❌ API_ID مطلوب! احصل عليه من my.telegram.org")
        
        if not self.api_hash:
            raise ValueError("❌ API_HASH مطلوب! احصل عليه من my.telegram.org")
        
        # استخراج bot_id من token إذا لم يُحدد
        if not self.bot_id:
            try:
                self.bot_id = int(self.bot_token.split(":")[0])
            except:
                self.bot_id = 0

@dataclass
class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    
    # نوع قاعدة البيانات
    db_type: str = os.getenv("DATABASE_TYPE", "sqlite")
    
    # SQLite
    sqlite_path: str = os.getenv("DATABASE_PATH", "zemusic_enhanced.db")
    
    # PostgreSQL (للمشاريع الكبيرة)
    postgres_url: Optional[str] = os.getenv("DATABASE_URL")
    postgres_host: str = os.getenv("DB_HOST", "localhost")
    postgres_port: int = int(os.getenv("DB_PORT", "5432"))
    postgres_name: str = os.getenv("DB_NAME", "zemusic")
    postgres_user: str = os.getenv("DB_USER", "postgres")
    postgres_password: str = os.getenv("DB_PASSWORD", "")
    
    # إعدادات الأداء
    enable_cache: bool = os.getenv("ENABLE_DATABASE_CACHE", "True").lower() == "true"
    cache_size: int = int(os.getenv("CACHE_SIZE", "1000"))
    connection_pool_size: int = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    
    # النسخ الاحتياطي التلقائي
    auto_backup: bool = os.getenv("AUTO_BACKUP", "True").lower() == "true"
    backup_interval: int = int(os.getenv("BACKUP_INTERVAL", "3600"))  # ثانية
    backup_keep_count: int = int(os.getenv("BACKUP_KEEP_COUNT", "24"))

@dataclass
class MusicConfig:
    """إعدادات الموسيقى والتشغيل"""
    
    # حدود التشغيل
    duration_limit: int = int(os.getenv("DURATION_LIMIT", "28800"))  # 8 ساعات
    playlist_limit: int = int(os.getenv("PLAYLIST_LIMIT", "100"))
    queue_limit: int = int(os.getenv("QUEUE_LIMIT", "50"))
    
    # جودة الصوت
    audio_quality: str = os.getenv("AUDIO_QUALITY", "high")  # low, medium, high, ultra
    video_quality: str = os.getenv("VIDEO_QUALITY", "720p")  # 480p, 720p, 1080p
    
    # أحجام الملفات
    max_audio_size: int = int(os.getenv("MAX_AUDIO_SIZE", "104857600"))  # 100MB
    max_video_size: int = int(os.getenv("MAX_VIDEO_SIZE", "2147483648"))  # 2GB
    
    # المنصات المدعومة
    enable_youtube: bool = os.getenv("ENABLE_YOUTUBE", "True").lower() == "true"
    enable_spotify: bool = os.getenv("ENABLE_SPOTIFY", "True").lower() == "true"
    enable_soundcloud: bool = os.getenv("ENABLE_SOUNDCLOUD", "True").lower() == "true"
    enable_apple_music: bool = os.getenv("ENABLE_APPLE_MUSIC", "False").lower() == "true"
    enable_resso: bool = os.getenv("ENABLE_RESSO", "False").lower() == "true"
    
    # إعدادات التحميل
    download_path: str = os.getenv("DOWNLOAD_PATH", "downloads")
    temp_path: str = os.getenv("TEMP_PATH", "temp")
    cleanup_interval: int = int(os.getenv("CLEANUP_INTERVAL", "1800"))  # 30 دقيقة

@dataclass
class AssistantConfig:
    """إعدادات الحسابات المساعدة"""
    
    # حدود الحسابات
    max_assistants: int = int(os.getenv("MAX_ASSISTANTS", "50"))
    min_assistants: int = int(os.getenv("MIN_ASSISTANTS", "1"))
    
    # إدارة تلقائية
    auto_management: bool = os.getenv("AUTO_ASSISTANT_MANAGEMENT", "True").lower() == "true"
    auto_leave_time: int = int(os.getenv("AUTO_LEAVE_TIME", "1800"))  # 30 دقيقة
    
    # توزيع الأحمال
    load_balancing: bool = os.getenv("LOAD_BALANCING", "True").lower() == "true"
    max_calls_per_assistant: int = int(os.getenv("MAX_CALLS_PER_ASSISTANT", "5"))
    
    # مراقبة الصحة
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # 5 دقائق
    reconnect_attempts: int = int(os.getenv("RECONNECT_ATTEMPTS", "3"))
    
    # مجلد الجلسات
    sessions_dir: str = os.getenv("SESSIONS_DIR", "telethon_sessions")

@dataclass
class SecurityConfig:
    """إعدادات الأمان والحماية"""
    
    # حماية من البريد المزعج
    anti_spam: bool = os.getenv("ANTI_SPAM", "True").lower() == "true"
    spam_threshold: int = int(os.getenv("SPAM_THRESHOLD", "5"))  # رسائل في الدقيقة
    spam_ban_duration: int = int(os.getenv("SPAM_BAN_DURATION", "3600"))  # ثانية
    
    # حماية من الفلود
    flood_protection: bool = os.getenv("FLOOD_PROTECTION", "True").lower() == "true"
    flood_threshold: int = int(os.getenv("FLOOD_THRESHOLD", "10"))
    
    # المستخدمين المحظورين
    banned_users: List[int] = field(default_factory=list)
    banned_chats: List[int] = field(default_factory=list)
    
    # الإذن للمجموعات الخاصة فقط
    private_groups_only: bool = os.getenv("PRIVATE_GROUPS_ONLY", "False").lower() == "true"
    
    # تشفير الجلسات
    encrypt_sessions: bool = os.getenv("ENCRYPT_SESSIONS", "True").lower() == "true"
    encryption_key: Optional[str] = os.getenv("ENCRYPTION_KEY")

@dataclass
class ChannelsConfig:
    """إعدادات القنوات والدعم"""
    
    # قنوات الاشتراك الإجباري
    force_subscribe_channels: List[str] = field(default_factory=lambda: [
        os.getenv("FORCE_SUBSCRIBE_CHANNEL", "")
    ])
    
    # قناة السجلات
    log_channel: Optional[int] = None
    
    # قناة التخزين المؤقت
    cache_channel: Optional[str] = os.getenv("CACHE_CHANNEL", "")
    
    # معلومات الدعم
    support_chat: str = os.getenv("SUPPORT_CHAT", "")
    support_channel: str = os.getenv("SUPPORT_CHANNEL", "")
    
    # معلومات المطور
    developer_channel: str = os.getenv("DEVELOPER_CHANNEL", "")
    updates_channel: str = os.getenv("UPDATES_CHANNEL", "")
    
    def __post_init__(self):
        """معالجة قناة السجلات"""
        log_id = os.getenv("LOGGER_ID")
        if log_id:
            try:
                self.log_channel = int(log_id)
            except ValueError:
                self.log_channel = None

@dataclass
class APIKeysConfig:
    """إعدادات مفاتيح API للخدمات الخارجية"""
    
    # YouTube Data API
    youtube_api_keys: List[str] = field(default_factory=lambda: [
        "AIzaSyA3x5N5DNYzd5j7L7JMn9XsUYil32Ak77U",
        "AIzaSyDw09GqGziUHXZ3FjugOypSXD7tedWzIzQ"
    ])
    
    # Spotify API
    spotify_client_id: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    # SoundCloud API
    soundcloud_client_id: Optional[str] = os.getenv("SOUNDCLOUD_CLIENT_ID")
    
    # Apple Music API
    apple_music_key: Optional[str] = os.getenv("APPLE_MUSIC_KEY")
    
    # Genius API (للكلمات)
    genius_api_key: Optional[str] = os.getenv("GENIUS_API_KEY")
    
    def __post_init__(self):
        """تحميل مفاتيح YouTube من متغير البيئة"""
        keys_env = os.getenv("YOUTUBE_API_KEYS")
        if keys_env:
            try:
                self.youtube_api_keys = json.loads(keys_env)
            except json.JSONDecodeError:
                pass

@dataclass
class ServerConfig:
    """إعدادات الخادم والشبكة"""
    
    # خوادم Invidious
    invidious_servers: List[str] = field(default_factory=lambda: [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de", 
        "https://yewtu.be",
        "https://invidious.f5.si",
        "https://invidious.materialio.us"
    ])
    
    # إعدادات الشبكة
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # إعدادات الكوكيز
    cookies_files: List[str] = field(default_factory=list)
    cookies_rotation: bool = os.getenv("COOKIES_ROTATION", "True").lower() == "true"
    
    # إعدادات البروكسي (اختياري)
    use_proxy: bool = os.getenv("USE_PROXY", "False").lower() == "true"
    proxy_url: Optional[str] = os.getenv("PROXY_URL")
    
    def __post_init__(self):
        """تحميل إعدادات الخوادم من متغيرات البيئة"""
        # تحميل خوادم Invidious
        servers_env = os.getenv("INVIDIOUS_SERVERS")
        if servers_env:
            try:
                self.invidious_servers = json.loads(servers_env)
            except json.JSONDecodeError:
                pass
        
        # تحميل ملفات الكوكيز
        cookies_env = os.getenv("COOKIES_FILES")
        if cookies_env:
            try:
                self.cookies_files = json.loads(cookies_env)
            except json.JSONDecodeError:
                pass
        else:
            # البحث عن ملفات الكوكيز في المجلد
            cookies_dir = Path("cookies")
            if cookies_dir.exists():
                self.cookies_files = [
                    str(f) for f in cookies_dir.glob("*.txt") if f.is_file()
                ]

@dataclass
class PerformanceConfig:
    """إعدادات الأداء والتحسين"""
    
    # إعدادات الذاكرة
    max_memory_usage: int = int(os.getenv("MAX_MEMORY_MB", "2048"))  # MB
    garbage_collection_interval: int = int(os.getenv("GC_INTERVAL", "300"))  # ثانية
    
    # إعدادات المعالجة المتوازية
    max_concurrent_downloads: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
    max_concurrent_streams: int = int(os.getenv("MAX_CONCURRENT_STREAMS", "20"))
    
    # إعدادات الكاش
    enable_redis: bool = os.getenv("ENABLE_REDIS", "False").lower() == "true"
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    
    # تحسينات خاصة للأحمال الكبيرة
    high_load_mode: bool = os.getenv("HIGH_LOAD_MODE", "True").lower() == "true"
    batch_processing: bool = os.getenv("BATCH_PROCESSING", "True").lower() == "true"

@dataclass
class LoggingConfig:
    """إعدادات السجلات والمراقبة"""
    
    # مستوى السجلات
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ملفات السجلات
    log_to_file: bool = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    log_file_path: str = os.getenv("LOG_FILE", "zemusic.log")
    max_log_size: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # سجلات مفصلة
    detailed_errors: bool = os.getenv("DETAILED_ERRORS", "True").lower() == "true"
    log_user_actions: bool = os.getenv("LOG_USER_ACTIONS", "True").lower() == "true"
    
    # مراقبة الأداء
    performance_monitoring: bool = os.getenv("PERFORMANCE_MONITORING", "True").lower() == "true"
    metrics_interval: int = int(os.getenv("METRICS_INTERVAL", "300"))  # ثانية

# ============================================
# الفئة الرئيسية للإعدادات
# ============================================

class EnhancedConfig:
    """إعدادات شاملة ومحسنة لبوت ZeMusic"""
    
    def __init__(self):
        """تهيئة جميع إعدادات البوت"""
        
        # تحميل الإعدادات
        self.system = SystemConfig()
        self.database = DatabaseConfig()
        self.music = MusicConfig()
        self.assistant = AssistantConfig()
        self.security = SecurityConfig()
        self.channels = ChannelsConfig()
        self.api_keys = APIKeysConfig()
        self.server = ServerConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
        
        # إنشاء المجلدات المطلوبة
        self._create_directories()
        
        # التحقق من صحة الإعدادات
        self._validate_config()
        
        # إعداد نظام السجلات
        self._setup_logging()
    
    def _create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = [
            self.music.download_path,
            self.music.temp_path,
            self.assistant.sessions_dir,
            "logs",
            "backups",
            "cookies"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def _validate_config(self):
        """التحقق من صحة الإعدادات"""
        
        # التحقق من الإعدادات الأساسية
        if not self.system.bot_token:
            raise ValueError("❌ BOT_TOKEN مطلوب!")
        
        # التحقق من حدود النظام للأحمال الكبيرة
        if self.performance.high_load_mode:
            # زيادة الحدود للأحمال الكبيرة
            self.music.queue_limit = min(self.music.queue_limit, 100)
            self.assistant.max_assistants = min(self.assistant.max_assistants, 50)
            self.performance.max_concurrent_streams = min(self.performance.max_concurrent_streams, 30)
        
        # التحقق من قنوات الاشتراك الإجباري
        self.channels.force_subscribe_channels = [
            ch for ch in self.channels.force_subscribe_channels if ch
        ]
    
    def _setup_logging(self):
        """إعداد نظام السجلات"""
        
        # تحديد مستوى السجلات
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        level = level_map.get(self.logging.log_level.upper(), logging.INFO)
        
        # إعداد التنسيق
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # إعداد المعالج للكونسول
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # إعداد المعالج للملف
        if self.logging.log_to_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.logging.log_file_path,
                maxBytes=self.logging.max_log_size,
                backupCount=self.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
        
        # تطبيق الإعدادات
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(console_handler)
        
        if self.logging.log_to_file:
            root_logger.addHandler(file_handler)
    
    def get_bot_info(self) -> Dict[str, Any]:
        """الحصول على معلومات البوت"""
        return {
            'name': self.system.bot_name,
            'username': self.system.bot_username,
            'id': self.system.bot_id,
            'owner_id': self.system.owner_id,
            'version': self.system.app_version,
            'language': self.system.default_language
        }
    
    def get_limits(self) -> Dict[str, Any]:
        """الحصول على حدود النظام"""
        return {
            'duration': self.music.duration_limit,
            'playlist': self.music.playlist_limit,
            'queue': self.music.queue_limit,
            'assistants': self.assistant.max_assistants,
            'audio_size': self.music.max_audio_size,
            'video_size': self.music.max_video_size
        }
    
    def is_high_performance_mode(self) -> bool:
        """فحص ما إذا كان البوت في وضع الأداء العالي"""
        return self.performance.high_load_mode
    
    def get_supported_platforms(self) -> List[str]:
        """الحصول على قائمة المنصات المدعومة"""
        platforms = []
        
        if self.music.enable_youtube:
            platforms.append("YouTube")
        if self.music.enable_spotify:
            platforms.append("Spotify")
        if self.music.enable_soundcloud:
            platforms.append("SoundCloud")
        if self.music.enable_apple_music:
            platforms.append("Apple Music")
        if self.music.enable_resso:
            platforms.append("Resso")
        
        return platforms

# ============================================
# إنشاء كائن الإعدادات العام
# ============================================

# إنشاء كائن الإعدادات الرئيسي
config = EnhancedConfig()

# متغيرات للتوافق مع الكود القديم
API_ID = config.system.api_id
API_HASH = config.system.api_hash
BOT_TOKEN = config.system.bot_token
BOT_NAME = config.system.bot_name
BOT_USERNAME = config.system.bot_username
BOT_ID = config.system.bot_id
OWNER_ID = config.system.owner_id

# إعدادات قاعدة البيانات
DATABASE_PATH = config.database.sqlite_path
DATABASE_TYPE = config.database.db_type
ENABLE_DATABASE_CACHE = config.database.enable_cache

# إعدادات الموسيقى
DURATION_LIMIT = config.music.duration_limit
DURATION_LIMIT_MIN = DURATION_LIMIT // 60
PLAYLIST_FETCH_LIMIT = config.music.playlist_limit

# إعدادات الحسابات المساعدة
MAX_ASSISTANTS = config.assistant.max_assistants
AUTO_LEAVING_ASSISTANT = config.assistant.auto_leave_time > 0

# إعدادات القنوات
LOGGER_ID = config.channels.log_channel
SUPPORT_CHAT = config.channels.support_chat

# قوائم المحظورين (للتوافق)
BANNED_USERS = set()

# رسالة عدم وجود مساعد
ASSISTANT_NOT_FOUND_MESSAGE = """
⚠️ **عذراً، لا يمكن تشغيل الموسيقى حالياً**

🚫 **المشكلة:** لا يوجد حساب مساعد متاح لتشغيل الموسيقى

📱 **ملاحظة:** يحتاج البوت لحسابات مساعدة لتشغيل الموسيقى في المكالمات الصوتية

📞 **للحصول على المساعدة:**
🔗 مجموعة الدعم: {support_chat}
👤 مطور البوت: [المطور](tg://user?id={owner_id})

⏰ **باقي وظائف البوت متاحة:** البحث، الأوامر، إدارة المجموعات

🔧 سيتم حل المشكلة في أقرب وقت ممكن
""".format(
    support_chat=SUPPORT_CHAT or "@YourSupport",
    owner_id=OWNER_ID
)

# دالة للتحقق من المستخدمين المحظورين
def is_banned_user(user_id: int) -> bool:
    """فحص ما إذا كان المستخدم محظور"""
    return user_id in BANNED_USERS

# دالة لإضافة مستخدم للحظر
def ban_user(user_id: int):
    """إضافة مستخدم للحظر"""
    BANNED_USERS.add(user_id)

# دالة لإلغاء حظر مستخدم
def unban_user(user_id: int):
    """إلغاء حظر مستخدم"""
    BANNED_USERS.discard(user_id)

# معلومات النسخة
__version__ = "3.0.0"
__author__ = "ZeMusic Team"
__description__ = "بوت موسيقى تلجرام متطور مع Telethon - نسخة محسنة للأحمال الكبيرة"

print(f"""
╔══════════════════════════════════════╗
║  🎵 ZeMusic Bot Enhanced Config 🎵   ║
╠══════════════════════════════════════╣
║                                      ║
║  📊 النسخة: {__version__}                     ║
║  🔧 وضع الأداء العالي: {'✅' if config.performance.high_load_mode else '❌'}           ║
║  📱 الحد الأقصى للمساعدين: {MAX_ASSISTANTS}           ║
║  🎵 المنصات المدعومة: {len(config.get_supported_platforms())}               ║
║                                      ║
║  🚀 مُحسن للعمل مع 7000 مجموعة       ║
║     و 70000 مستخدم                  ║
║                                      ║
╚══════════════════════════════════════╝
""")