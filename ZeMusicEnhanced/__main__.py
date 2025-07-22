#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot Enhanced - Main Entry Point
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Telethon Enhanced Edition

الملف الرئيسي لتشغيل بوت الموسيقى المحسن
مُحسن للعمل مع 7000 مجموعة و 70000 مستخدم
"""

import asyncio
import logging
import signal
import sys
import os
from contextlib import suppress
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# تحميل الإعدادات والمكونات
try:
    from config_enhanced import config
    from ZeMusicEnhanced import (
        initialize_bot, shutdown_bot, get_bot_info, get_system_status,
        telethon_manager, database_manager, music_manager, performance_monitor
    )
    from ZeMusicEnhanced.core.enhanced_bot import EnhancedZeMusicBot
except ImportError as e:
    print(f"❌ خطأ في تحميل المكونات: {e}")
    print("💡 تأكد من تثبيت المتطلبات: pip install -r requirements_enhanced.txt")
    sys.exit(1)

# إعداد نظام السجلات
logging.basicConfig(
    level=getattr(logging, config.logging.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class ZeMusicBotRunner:
    """مشغل البوت المحسن مع إدارة متقدمة للعمليات"""
    
    def __init__(self):
        self.bot = None
        self.is_running = False
        self.startup_time = None
        self.shutdown_requested = False
        
    async def initialize(self):
        """تهيئة البوت وجميع مكوناته"""
        try:
            logger.info("🚀 بدء تهيئة ZeMusic Bot Enhanced...")
            
            # عرض معلومات النظام
            self._show_system_info()
            
            # التحقق من المتطلبات
            if not self._check_requirements():
                return False
            
            # إنشاء البوت المحسن
            self.bot = EnhancedZeMusicBot()
            
            # تهيئة البوت
            success = await self.bot.initialize()
            if not success:
                logger.error("❌ فشل في تهيئة البوت")
                return False
            
            # إعداد معالجات الإشارات
            self._setup_signal_handlers()
            
            # تسجيل وقت البدء
            self.startup_time = asyncio.get_event_loop().time()
            self.is_running = True
            
            logger.info("✅ تم تهيئة ZeMusic Bot Enhanced بنجاح!")
            self._show_startup_message()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت: {e}")
            return False
    
    def _show_system_info(self):
        """عرض معلومات النظام"""
        info = get_bot_info()
        
        system_info = f"""
╔══════════════════════════════════════╗
║       🔧 معلومات النظام 🔧           ║
╠══════════════════════════════════════╣
║                                      ║
║  🐍 Python: {info['python_version']}                    ║
║  🎵 ZeMusic: {info['version']}                   ║
║  🔥 Telethon: 1.36.0                 ║
║  💾 قاعدة البيانات: {config.database.db_type.upper()}            ║
║                                      ║
║  ⚡ وضع الأداء العالي: {'✅' if config.performance.high_load_mode else '❌'}           ║
║  📱 الحد الأقصى للمساعدين: {config.assistant.max_assistants}           ║
║  🎯 المنصات المدعومة: {len(config.get_supported_platforms())}               ║
║                                      ║
╚══════════════════════════════════════╝
        """
        print(system_info)
    
    def _check_requirements(self):
        """فحص المتطلبات الأساسية"""
        try:
            # فحص Python version
            if sys.version_info < (3, 8):
                logger.error("❌ Python 3.8+ مطلوب!")
                return False
            
            # فحص الإعدادات الأساسية
            if not config.system.bot_token:
                logger.error("❌ BOT_TOKEN غير محدد!")
                return False
            
            if not config.system.api_id or not config.system.api_hash:
                logger.error("❌ API_ID أو API_HASH غير محدد!")
                return False
            
            # فحص المجلدات المطلوبة
            required_dirs = [
                config.music.download_path,
                config.music.temp_path,
                config.assistant.sessions_dir,
                "logs",
                "backups"
            ]
            
            for directory in required_dirs:
                Path(directory).mkdir(exist_ok=True)
            
            logger.info("✅ جميع المتطلبات متوفرة")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص المتطلبات: {e}")
            return False
    
    def _setup_signal_handlers(self):
        """إعداد معالجات الإشارات للإيقاف الآمن"""
        def signal_handler(signum, frame):
            logger.info(f"🔔 تم استلام إشارة الإيقاف: {signum}")
            self.shutdown_requested = True
            asyncio.create_task(self.shutdown())
        
        # إعداد معالجات الإشارات
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # معالج خاص لـ Windows
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def _show_startup_message(self):
        """عرض رسالة بدء التشغيل"""
        status = get_system_status()
        
        # حساب الإحصائيات
        assistants_count = 0
        connected_assistants = 0
        active_sessions = 0
        
        if telethon_manager:
            assistants_count = telethon_manager.get_assistants_count()
            connected_assistants = telethon_manager.get_connected_assistants_count()
        
        if music_manager:
            active_sessions = len(music_manager.active_sessions)
        
        startup_message = f"""
╔══════════════════════════════════════╗
║     🎵 ZeMusic Enhanced جاهز! 🎵     ║
╠══════════════════════════════════════╣
║                                      ║
║  ✅ البوت الرئيسي: متصل              ║
║  📱 الحسابات المساعدة: {assistants_count} ({connected_assistants} متصل)     ║
║  💾 قاعدة البيانات: {'✅' if status['database_manager'] else '❌'}              ║
║  🎵 جلسات التشغيل: {active_sessions}                ║
║  📊 مراقب الأداء: {'✅' if status['performance_monitor'] else '❌'}              ║
║                                      ║
║  🎯 الوظائف المتاحة:                 ║
║     {'✅ تشغيل الموسيقى' if assistants_count > 0 else '⚠️ تشغيل محدود (بحاجة لمساعدين)'}               ║
║     ✅ إدارة المجموعات                ║
║     ✅ الأوامر الإدارية               ║
║     ✅ الإحصائيات المتقدمة            ║
║     ✅ النسخ الاحتياطي التلقائي       ║
║                                      ║
║  🔥 مُحسن للأحمال الكبيرة:           ║
║     📊 يدعم حتى 7000 مجموعة          ║
║     👥 يدعم حتى 70000 مستخدم         ║
║                                      ║
║  📞 الدعم: {config.channels.support_chat or '@YourSupport'}               ║
║                                      ║
╚══════════════════════════════════════╝
        """
        print(startup_message)
        
        # تحذيرات إضافية
        if assistants_count == 0:
            print("⚠️ تحذير: لا توجد حسابات مساعدة - استخدم /owner لإضافة حسابات")
        
        if not config.performance.high_load_mode:
            print("💡 نصيحة: فعل وضع الأداء العالي للحصول على أفضل أداء")
    
    async def run(self):
        """تشغيل البوت الرئيسي"""
        try:
            if not self.bot:
                logger.error("❌ البوت غير مُهيأ!")
                return
            
            logger.info("🎵 بدء تشغيل ZeMusic Bot Enhanced...")
            
            # بدء البوت
            await self.bot.start()
            
            # الحفاظ على التشغيل
            while self.is_running and not self.shutdown_requested:
                await asyncio.sleep(1)
                
                # فحص صحة النظام كل 5 دقائق
                if asyncio.get_event_loop().time() % 300 < 1:
                    await self._health_check()
            
        except KeyboardInterrupt:
            logger.info("⌨️ تم استلام إشارة إيقاف من المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        finally:
            await self.shutdown()
    
    async def _health_check(self):
        """فحص دوري لصحة النظام"""
        try:
            status = get_system_status()
            
            if not status['overall_ready']:
                logger.warning("⚠️ النظام غير مستقر - محاولة إصلاح...")
                
                # محاولة إعادة تشغيل المكونات المعطلة
                if not status['telethon_manager'] and telethon_manager:
                    await telethon_manager.reconnect()
                
                if not status['music_manager'] and music_manager:
                    await music_manager.restart()
            
            # تنظيف الذاكرة
            if performance_monitor:
                await performance_monitor.cleanup_memory()
                
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الصحة: {e}")
    
    async def shutdown(self):
        """إيقاف البوت بأمان"""
        if self.shutdown_requested:
            return
        
        self.shutdown_requested = True
        self.is_running = False
        
        try:
            logger.info("🛑 بدء إيقاف ZeMusic Bot Enhanced...")
            
            # إيقاف البوت
            if self.bot:
                await self.bot.shutdown()
            
            # إيقاف المكونات الأساسية
            await shutdown_bot()
            
            # حساب وقت التشغيل
            if self.startup_time:
                uptime = asyncio.get_event_loop().time() - self.startup_time
                logger.info(f"⏱️ إجمالي وقت التشغيل: {uptime:.2f} ثانية")
            
            logger.info("✅ تم إيقاف البوت بأمان")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف البوت: {e}")

async def main():
    """الدالة الرئيسية"""
    try:
        # إعداد حلقة الأحداث
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # إنشاء مشغل البوت
        runner = ZeMusicBotRunner()
        
        # تهيئة البوت
        success = await runner.initialize()
        if not success:
            logger.error("❌ فشل في تهيئة البوت")
            sys.exit(1)
        
        # تشغيل البوت
        await runner.run()
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ فادح في البوت: {e}")
        sys.exit(1)

def run_bot():
    """دالة مساعدة لتشغيل البوت"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 وداعاً!")
    except Exception as e:
        print(f"❌ خطأ فادح: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # عرض معلومات البوت
    info = get_bot_info()
    print(f"""
🎵 ZeMusic Bot Enhanced v{info['version']}
👨‍💻 بواسطة: {info['author']}
🔥 مدعوم بـ Telethon v1.36.0

🚀 بدء التشغيل...
    """)
    
    # تشغيل البوت
    run_bot()