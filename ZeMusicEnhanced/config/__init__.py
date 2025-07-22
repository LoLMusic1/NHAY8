#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Configuration System
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Enhanced Edition

نظام إعدادات شامل ومحسن لبوت الموسيقى
مصمم للعمل مع 7000 مجموعة و 70000 مستخدم
"""

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
class TelegramConfig:
    """إعدادات Telegram API"""
    api_id: int = int(os.getenv("API_ID", "0"))
    api_hash: str = os.getenv("API_HASH", "")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    bot_username: str = os.getenv("BOT_USERNAME", "")
    
    # معلومات الجهاز للتخفي
    device_model: str = os.getenv("DEVICE_MODEL", "ZeMusic Enhanced Server")
    system_version: str = os.getenv("SYSTEM_VERSION", "Ubuntu 22.04 LTS")
    app_version: str = os.getenv("APP_VERSION", "3.0.0")
    
    def __post_init__(self):
        if not self.api_id or not self.api_hash or not self.bot_token:
            raise ValueError("❌ API_ID, API_HASH, BOT_TOKEN مطلوبة!")

@dataclass
class OwnerConfig:
    """إعدادات المالك والمطورين"""
    owner_id: int = int(os.getenv("OWNER_ID", "0"))
    owner_username: str = os.getenv("OWNER_USERNAME", "")
    sudo_users: List[int] = field(default_factory=list)
    developer_ids: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.owner_id:
            raise ValueError("❌ OWNER_ID مطلوب!")
        
        # تحميل المطورين من متغير البيئة
        sudo_env = os.getenv("SUDO_USERS")
        if sudo_env:
            try:
                self.sudo_users = [int(x.strip()) for x in sudo_env.split(",") if x.strip()]
            except ValueError:
                pass

@dataclass
class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    # نوع قاعدة البيانات
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///zemusic_enhanced.db")
    
    # إعدادات الأداء
    enable_cache: bool = os.getenv("ENABLE_DATABASE_CACHE", "True").lower() == "true"
    cache_size: int = int(os.getenv("CACHE_SIZE", "2000"))
    connection_pool_size: int = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
    
    # النسخ الاحتياطي
    auto_backup: bool = os.getenv("AUTO_BACKUP", "True").lower() == "true"
    backup_interval: int = int(os.getenv("BACKUP_INTERVAL", "3600"))  # ثانية
    backup_keep_count: int = int(os.getenv("BACKUP_KEEP_COUNT", "48"))  # 2 يوم
    
    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")
    
    @property
    def is_postgresql(self) -> bool:
        return self.database_url.startswith("postgresql")

@dataclass
class AssistantConfig:
    """إعدادات الحسابات المساعدة"""
    # حدود الحسابات
    max_assistants: int = int(os.getenv("MAX_ASSISTANTS", "50"))
    min_assistants: int = int(os.getenv("MIN_ASSISTANTS", "2"))
    
    # إدارة تلقائية
    auto_management: bool = os.getenv("AUTO_ASSISTANT_MANAGEMENT", "True").lower() == "true"
    auto_leave_time: int = int(os.getenv("AUTO_LEAVE_TIME", "1800"))  # 30 دقيقة
    
    # توزيع الأحمال
    load_balancing: bool = os.getenv("LOAD_BALANCING", "True").lower() == "true"
    max_calls_per_assistant: int = int(os.getenv("MAX_CALLS_PER_ASSISTANT", "3"))
    
    # مراقبة الصحة
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # 5 دقائق
    reconnect_attempts: int = int(os.getenv("RECONNECT_ATTEMPTS", "5"))
    
    # مجلد الجلسات
    sessions_dir: str = os.getenv("SESSIONS_DIR", "sessions")
    
    # جلسات الحسابات المساعدة
    session_strings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # تحميل جلسات الحسابات المساعدة
        for i in range(1, self.max_assistants + 1):
            session = os.getenv(f"ASSISTANT_SESSION_{i}")
            if session:
                self.session_strings.append(session)

@dataclass
class MusicConfig:
    """إعدادات الموسيقى والتشغيل"""
    # حدود التشغيل
    duration_limit: int = int(os.getenv("DURATION_LIMIT", "32400"))  # 9 ساعات
    playlist_limit: int = int(os.getenv("PLAYLIST_LIMIT", "200"))
    queue_limit: int = int(os.getenv("QUEUE_LIMIT", "100"))
    
    # جودة الصوت والفيديو
    audio_quality: str = os.getenv("AUDIO_QUALITY", "high")  # low, medium, high, ultra
    video_quality: str = os.getenv("VIDEO_QUALITY", "720p")  # 480p, 720p, 1080p
    
    # أحجام الملفات
    max_audio_size: int = int(os.getenv("MAX_AUDIO_SIZE", "157286400"))  # 150MB
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
    force_subscribe_channels: List[str] = field(default_factory=list)
    
    # قناة السجلات
    log_channel_id: Optional[int] = None
    
    # قناة التخزين المؤقت
    cache_channel_id: Optional[str] = os.getenv("CACHE_CHANNEL_ID")
    
    # معلومات الدعم
    support_chat: str = os.getenv("SUPPORT_CHAT", "")
    support_channel: str = os.getenv("SUPPORT_CHANNEL", "")
    
    # معلومات المطور
    developer_channel: str = os.getenv("DEVELOPER_CHANNEL", "")
    updates_channel: str = os.getenv("UPDATES_CHANNEL", "")
    
    def __post_init__(self):
        # معالجة قناة السجلات
        log_id = os.getenv("LOG_CHANNEL_ID")
        if log_id:
            try:
                self.log_channel_id = int(log_id)
            except ValueError:
                pass
        
        # معالجة قنوات الاشتراك الإجباري
        force_channels = os.getenv("FORCE_SUBSCRIBE_CHANNELS")
        if force_channels:
            self.force_subscribe_channels = [
                ch.strip() for ch in force_channels.split(",") if ch.strip()
            ]

@dataclass
class APIKeysConfig:
    """إعدادات مفاتيح API للخدمات الخارجية"""
    # YouTube Data API
    youtube_api_keys: List[str] = field(default_factory=lambda: [
        "AIzaSyA3x5N5DNYzd5j7L7JMn9XsUYil32Ak77U",
        "AIzaSyDw09GqGziUHXZ3FjugOypSXD7tedWzIzQ",
        "AIzaSyBkZRCr-8mZk0y8ZDwE8Jh5Y2I4J8K6L0M"
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
        # تحميل مفاتيح YouTube من متغير البيئة
        keys_env = os.getenv("YOUTUBE_API_KEYS")
        if keys_env:
            try:
                custom_keys = json.loads(keys_env)
                if isinstance(custom_keys, list):
                    self.youtube_api_keys = custom_keys
            except json.JSONDecodeError:
                pass

@dataclass
class PerformanceConfig:
    """إعدادات الأداء والتحسين"""
    # إعدادات الذاكرة
    max_memory_usage: int = int(os.getenv("MAX_MEMORY_MB", "4096"))  # 4GB
    garbage_collection_interval: int = int(os.getenv("GC_INTERVAL", "300"))  # ثانية
    
    # إعدادات المعالجة المتوازية
    max_concurrent_downloads: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "10"))
    max_concurrent_streams: int = int(os.getenv("MAX_CONCURRENT_STREAMS", "50"))
    
    # إعدادات الكاش
    enable_redis: bool = os.getenv("ENABLE_REDIS", "False").lower() == "true"
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    
    # تحسينات خاصة للأحمال الكبيرة
    high_load_mode: bool = os.getenv("HIGH_LOAD_MODE", "True").lower() == "true"
    batch_processing: bool = os.getenv("BATCH_PROCESSING", "True").lower() == "true"
    
    # إعدادات الشبكة
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "5"))

@dataclass
class LoggingConfig:
    """إعدادات السجلات والمراقبة"""
    # مستوى السجلات
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ملفات السجلات
    log_to_file: bool = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    log_file_path: str = os.getenv("LOG_FILE", "logs/zemusic_enhanced.log")
    max_log_size: int = int(os.getenv("MAX_LOG_SIZE", "52428800"))  # 50MB
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "10"))
    
    # سجلات مفصلة
    detailed_errors: bool = os.getenv("DETAILED_ERRORS", "True").lower() == "true"
    log_user_actions: bool = os.getenv("LOG_USER_ACTIONS", "True").lower() == "true"
    
    # مراقبة الأداء
    performance_monitoring: bool = os.getenv("PERFORMANCE_MONITORING", "True").lower() == "true"
    metrics_interval: int = int(os.getenv("METRICS_INTERVAL", "300"))  # ثانية

# ============================================
# الكلاس الرئيسي للإعدادات
# ============================================

class EnhancedConfig:
    """إعدادات شاملة ومحسنة لبوت ZeMusic v3.0"""
    
    def __init__(self):
        """تهيئة جميع إعدادات البوت"""
        
        # تحميل الإعدادات
        self.telegram = TelegramConfig()
        self.owner = OwnerConfig()
        self.database = DatabaseConfig()
        self.assistant = AssistantConfig()
        self.music = MusicConfig()
        self.security = SecurityConfig()
        self.channels = ChannelsConfig()
        self.api_keys = APIKeysConfig()
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
            "cookies",
            "assets"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def _validate_config(self):
        """التحقق من صحة الإعدادات"""
        
        # التحقق من الإعدادات الأساسية
        if not self.telegram.bot_token:
            raise ValueError("❌ BOT_TOKEN مطلوب!")
        
        if not self.owner.owner_id:
            raise ValueError("❌ OWNER_ID مطلوب!")
        
        # تحسينات للأحمال الكبيرة
        if self.performance.high_load_mode:
            # زيادة الحدود للأحمال الكبيرة
            self.music.queue_limit = min(self.music.queue_limit, 200)
            self.assistant.max_assistants = min(self.assistant.max_assistants, 50)
            self.performance.max_concurrent_streams = min(self.performance.max_concurrent_streams, 50)
    
    def _setup_logging(self):
        """إعداد نظام السجلات المتقدم"""
        
        # تحديد مستوى السجلات
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        level = level_map.get(self.logging.log_level.upper(), logging.INFO)
        
        # إعداد التنسيق المحسن
        formatter = logging.Formatter(
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # إعداد المعالج للكونسول
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # إعداد المعالج للملف
        if self.logging.log_to_file:
            from logging.handlers import RotatingFileHandler
            # إنشاء مجلد السجلات
            Path(self.logging.log_file_path).parent.mkdir(exist_ok=True)
            
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
        root_logger.handlers.clear()  # مسح المعالجات السابقة
        root_logger.addHandler(console_handler)
        
        if self.logging.log_to_file:
            root_logger.addHandler(file_handler)
    
    def get_bot_info(self) -> Dict[str, Any]:
        """الحصول على معلومات البوت"""
        return {
            'name': 'ZeMusic Enhanced',
            'version': '3.0.0',
            'owner_id': self.owner.owner_id,
            'max_assistants': self.assistant.max_assistants,
            'high_load_mode': self.performance.high_load_mode,
            'database_type': 'PostgreSQL' if self.database.is_postgresql else 'SQLite',
            'redis_enabled': self.performance.enable_redis,
            'supported_platforms': self._get_supported_platforms()
        }
    
    def _get_supported_platforms(self) -> List[str]:
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
        platforms.append("Telegram")  # دائماً مدعوم
        return platforms
    
    def is_owner(self, user_id: int) -> bool:
        """التحقق من كون المستخدم هو المالك"""
        return user_id == self.owner.owner_id
    
    def is_sudo(self, user_id: int) -> bool:
        """التحقق من كون المستخدم مطور"""
        return user_id in self.owner.sudo_users or self.is_owner(user_id)
    
    def is_banned(self, user_id: int) -> bool:
        """التحقق من كون المستخدم محظور"""
        return user_id in self.security.banned_users

# إنشاء مثيل عام للإعدادات
config = EnhancedConfig()

# تصدير الإعدادات للاستخدام السهل
__all__ = [
    'config',
    'EnhancedConfig',
    'TelegramConfig',
    'OwnerConfig',
    'DatabaseConfig',
    'AssistantConfig',
    'MusicConfig',
    'SecurityConfig',
    'ChannelsConfig',
    'APIKeysConfig',
    'PerformanceConfig',
    'LoggingConfig'
]