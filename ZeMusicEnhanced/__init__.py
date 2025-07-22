#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot Enhanced - Main Package Initialization
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Telethon Enhanced Edition

بوت موسيقى تلجرام متطور مع Telethon
مُحسن للعمل مع 7000 مجموعة و 70000 مستخدم
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# إضافة مسار المشروع للنظام
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# تحديد النسخة والمعلومات الأساسية
__version__ = "3.0.0"
__author__ = "ZeMusic Team"
__license__ = "MIT"
__description__ = "بوت موسيقى تلجرام متطور مع Telethon - محسن للأحمال الكبيرة"

# تحميل الإعدادات المحسنة
try:
    from config_enhanced import config
    CONFIG_LOADED = True
except ImportError:
    try:
        import config
        CONFIG_LOADED = True
    except ImportError:
        CONFIG_LOADED = False
        print("❌ لم يتم العثور على ملف الإعدادات!")

# إعداد نظام السجلات المبكر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# التحقق من إصدار Python
if sys.version_info < (3, 8):
    logger.error("❌ Python 3.8+ مطلوب! النسخة الحالية: %s", sys.version)
    sys.exit(1)

# التحقق من المتطلبات الأساسية
def check_requirements():
    """فحص المتطلبات الأساسية"""
    required_modules = [
        'telethon',
        'aiofiles',
        'aiohttp',
        'aiosqlite',
        'cryptg'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error("❌ المكتبات المطلوبة غير مثبتة: %s", ', '.join(missing_modules))
        logger.info("💡 لتثبيت المتطلبات: pip install -r requirements_enhanced.txt")
        return False
    
    return True

# فحص المتطلبات عند التحميل
REQUIREMENTS_OK = check_requirements()

# تحميل المكونات الأساسية
if CONFIG_LOADED and REQUIREMENTS_OK:
    try:
        # تحميل المكونات الأساسية
        from .core.enhanced_telethon_client import EnhancedTelethonManager
        from .core.enhanced_database import EnhancedDatabaseManager
        from .core.enhanced_music_manager import EnhancedMusicManager
        from .core.performance_monitor import PerformanceMonitor
        
        # تحميل معالجات الأوامر
        from .handlers.command_handler import EnhancedCommandHandler
        from .handlers.message_handler import EnhancedMessageHandler
        from .handlers.callback_handler import EnhancedCallbackHandler
        
        # تحميل الخدمات
        from .services.music_service import MusicService
        from .services.assistant_service import AssistantService
        from .services.cache_service import CacheService
        
        # تحميل منصات التشغيل
        from .platforms.youtube_enhanced import EnhancedYouTube
        from .platforms.spotify_enhanced import EnhancedSpotify
        from .platforms.soundcloud_enhanced import EnhancedSoundCloud
        
        COMPONENTS_LOADED = True
        logger.info("✅ تم تحميل جميع مكونات البوت بنجاح")
        
    except ImportError as e:
        COMPONENTS_LOADED = False
        logger.error("❌ خطأ في تحميل المكونات: %s", e)
else:
    COMPONENTS_LOADED = False

# إنشاء المتغيرات العامة
telethon_manager = None
database_manager = None
music_manager = None
performance_monitor = None

# دوال التهيئة
async def initialize_bot():
    """تهيئة البوت والمكونات الأساسية"""
    global telethon_manager, database_manager, music_manager, performance_monitor
    
    if not CONFIG_LOADED:
        raise RuntimeError("❌ ملف الإعدادات غير محمل!")
    
    if not REQUIREMENTS_OK:
        raise RuntimeError("❌ المتطلبات الأساسية غير مكتملة!")
    
    if not COMPONENTS_LOADED:
        raise RuntimeError("❌ مكونات البوت غير محملة!")
    
    try:
        logger.info("🚀 بدء تهيئة ZeMusic Bot Enhanced...")
        
        # تهيئة مراقب الأداء
        performance_monitor = PerformanceMonitor()
        await performance_monitor.start()
        
        # تهيئة قاعدة البيانات
        database_manager = EnhancedDatabaseManager()
        await database_manager.initialize()
        
        # تهيئة عميل Telethon
        telethon_manager = EnhancedTelethonManager()
        await telethon_manager.initialize()
        
        # تهيئة مدير الموسيقى
        music_manager = EnhancedMusicManager(
            telethon_manager=telethon_manager,
            database_manager=database_manager
        )
        await music_manager.initialize()
        
        logger.info("✅ تم تهيئة جميع مكونات البوت بنجاح")
        return True
        
    except Exception as e:
        logger.error("❌ خطأ في تهيئة البوت: %s", e)
        return False

async def shutdown_bot():
    """إيقاف البوت بأمان"""
    global telethon_manager, database_manager, music_manager, performance_monitor
    
    try:
        logger.info("🛑 بدء إيقاف البوت...")
        
        # إيقاف مدير الموسيقى
        if music_manager:
            await music_manager.shutdown()
        
        # إيقاف عميل Telethon
        if telethon_manager:
            await telethon_manager.shutdown()
        
        # إيقاف قاعدة البيانات
        if database_manager:
            await database_manager.close()
        
        # إيقاف مراقب الأداء
        if performance_monitor:
            await performance_monitor.stop()
        
        logger.info("✅ تم إيقاف البوت بأمان")
        
    except Exception as e:
        logger.error("❌ خطأ في إيقاف البوت: %s", e)

# دالة للحصول على معلومات البوت
def get_bot_info():
    """الحصول على معلومات البوت"""
    return {
        'name': 'ZeMusic Enhanced',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'license': __license__,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'config_loaded': CONFIG_LOADED,
        'requirements_ok': REQUIREMENTS_OK,
        'components_loaded': COMPONENTS_LOADED,
        'high_load_mode': config.performance.high_load_mode if CONFIG_LOADED else False,
        'max_assistants': config.assistant.max_assistants if CONFIG_LOADED else 0,
        'supported_platforms': config.get_supported_platforms() if CONFIG_LOADED else []
    }

# دالة للحصول على حالة النظام
def get_system_status():
    """الحصول على حالة النظام"""
    status = {
        'bot_ready': all([CONFIG_LOADED, REQUIREMENTS_OK, COMPONENTS_LOADED]),
        'telethon_manager': telethon_manager is not None and telethon_manager.is_ready if telethon_manager else False,
        'database_manager': database_manager is not None and database_manager.is_ready if database_manager else False,
        'music_manager': music_manager is not None and music_manager.is_ready if music_manager else False,
        'performance_monitor': performance_monitor is not None and performance_monitor.is_running if performance_monitor else False
    }
    
    status['overall_ready'] = all(status.values())
    return status

# رسالة الترحيب
def show_welcome_message():
    """عرض رسالة الترحيب"""
    info = get_bot_info()
    status = get_system_status()
    
    welcome_message = f"""
╔══════════════════════════════════════╗
║    🎵 ZeMusic Bot Enhanced 🎵        ║
╠══════════════════════════════════════╣
║                                      ║
║  📊 النسخة: {info['version']}                     ║
║  🐍 Python: {info['python_version']}                    ║
║  📦 الإعدادات: {'✅' if info['config_loaded'] else '❌'}                 ║
║  🔧 المتطلبات: {'✅' if info['requirements_ok'] else '❌'}                 ║
║  🧩 المكونات: {'✅' if info['components_loaded'] else '❌'}                  ║
║                                      ║
║  🚀 الحالة العامة: {'✅ جاهز' if status['overall_ready'] else '❌ غير جاهز'}            ║
║                                      ║
║  🎯 مُحسن للأحمال الكبيرة:           ║
║     📊 7000 مجموعة                   ║
║     👥 70000 مستخدم                  ║
║                                      ║
║  🔥 Powered by Telethon v1.36.0      ║
║                                      ║
╚══════════════════════════════════════╝
    """
    
    print(welcome_message)
    
    if not status['overall_ready']:
        print("⚠️ البوت غير جاهز للعمل! تحقق من الأخطاء أعلاه.")
    else:
        print("🎉 البوت جاهز للعمل!")

# عرض رسالة الترحيب عند التحميل
if __name__ != "__main__":
    show_welcome_message()

# تصدير المكونات الأساسية
__all__ = [
    # معلومات البوت
    '__version__',
    '__author__',
    '__license__',
    '__description__',
    
    # الحالة
    'CONFIG_LOADED',
    'REQUIREMENTS_OK', 
    'COMPONENTS_LOADED',
    
    # المديرين الأساسيين
    'telethon_manager',
    'database_manager',
    'music_manager',
    'performance_monitor',
    
    # الدوال الأساسية
    'initialize_bot',
    'shutdown_bot',
    'get_bot_info',
    'get_system_status',
    'show_welcome_message',
    
    # فحص المتطلبات
    'check_requirements'
]

# رسالة تطوير
if CONFIG_LOADED and hasattr(config, 'system') and config.system.owner_id:
    logger.info("👨‍💻 البوت مُعد للمالك: %s", config.system.owner_id)

# إعداد حلقة الأحداث للنظم التي تحتاجها
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger.info("📦 تم تحميل حزمة ZeMusic Enhanced بنجاح")