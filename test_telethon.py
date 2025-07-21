#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 اختبار Telethon - مشروع ZeMusic
تاريخ الإنشاء: 2025-01-28
"""

import sys
import asyncio
import os
from pathlib import Path

def test_telethon_import():
    """اختبار استيراد مكتبة Telethon"""
    
    print("🧪 بدء اختبار Telethon...")
    
    try:
        # اختبار استيراد Telethon
        print("📚 اختبار استيراد Telethon...")
        from telethon import TelegramClient, events
        from telethon.sessions import StringSession
        from telethon.errors import SessionPasswordNeededError
        print("✅ تم استيراد Telethon بنجاح")
        
        # عرض إصدار Telethon
        try:
            import telethon
            version = telethon.__version__
            print(f"🔖 إصدار Telethon: {version}")
        except:
            print("⚠️ لا يمكن تحديد إصدار Telethon")
        
        return True
        
    except ImportError as e:
        print(f"❌ خطأ في استيراد Telethon: {e}")
        print("💡 تأكد من تثبيت Telethon: pip install telethon")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False

async def test_telethon_client():
    """اختبار إنشاء عميل Telethon"""
    
    try:
        print("\n🔗 اختبار إنشاء عميل Telethon...")
        
        # استيراد Telethon هنا
        from telethon import TelegramClient
        
        # محاولة قراءة الإعدادات
        try:
            import config
            api_id = config.API_ID
            api_hash = config.API_HASH
            
            if not api_id or not api_hash:
                print("⚠️ API_ID أو API_HASH غير محدد في الإعدادات")
                return False
                
        except ImportError:
            print("⚠️ ملف config.py غير موجود، استخدام قيم تجريبية")
            api_id = 123456  # قيم تجريبية
            api_hash = "test_hash"
        
        # إنشاء مجلد الجلسات
        sessions_dir = "telethon_sessions"
        os.makedirs(sessions_dir, exist_ok=True)
        print(f"📁 مجلد الجلسات: {Path(sessions_dir).absolute()}")
        
        # إنشاء عميل تجريبي
        client = TelegramClient(
            session=f"{sessions_dir}/test_session",
            api_id=api_id,
            api_hash=api_hash,
            device_model="ZeMusic Test",
            system_version="Ubuntu 20.04",
            app_version="2.0.0",
            lang_code="ar",
            system_lang_code="ar"
        )
        
        print("✅ تم إنشاء عميل Telethon بنجاح")
        
        # اختبار الاتصال (بدون تسجيل دخول)
        print("🌐 اختبار الاتصال...")
        await client.connect()
        
        if client.is_connected():
            print("✅ تم الاتصال بخوادم Telegram بنجاح")
        else:
            print("❌ فشل الاتصال بخوادم Telegram")
            return False
        
        # قطع الاتصال
        await client.disconnect()
        print("🔌 تم قطع الاتصال")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار العميل: {e}")
        return False

def test_telethon_manager():
    """اختبار مدير Telethon"""
    
    try:
        print("\n🎛️ اختبار مدير Telethon...")
        
        # استيراد المدير
        from ZeMusic.core.telethon_client import telethon_manager
        print("✅ تم استيراد مدير Telethon بنجاح")
        
        # اختبار الخصائص الأساسية
        print(f"📊 عدد الحسابات المساعدة: {telethon_manager.get_assistants_count()}")
        print(f"🔗 عدد الحسابات المتصلة: {telethon_manager.get_connected_assistants_count()}")
        print(f"📁 مجلد الجلسات: {telethon_manager.sessions_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار المدير: {e}")
        return False

def get_telethon_info():
    """عرض معلومات Telethon"""
    
    print("\n📋 معلومات Telethon:")
    
    try:
        import telethon
        print(f"📦 إصدار Telethon: {telethon.__version__}")
        print(f"📍 مسار Telethon: {telethon.__file__}")
        
        # معلومات الجلسات
        sessions_dir = Path("telethon_sessions")
        if sessions_dir.exists():
            print(f"\n📁 مجلد الجلسات: {sessions_dir.absolute()}")
            session_files = list(sessions_dir.glob("*.session"))
            print(f"📄 عدد ملفات الجلسات: {len(session_files)}")
            
            if session_files:
                print("\n🔍 ملفات الجلسات الموجودة:")
                for session_file in session_files:
                    size = session_file.stat().st_size / 1024  # KB
                    print(f"   • {session_file.name} ({size:.1f} KB)")
        
        # معلومات الإعدادات
        try:
            import config
            print(f"\n⚙️ الإعدادات:")
            print(f"   • API_ID: {'✅ محدد' if config.API_ID else '❌ غير محدد'}")
            print(f"   • API_HASH: {'✅ محدد' if config.API_HASH else '❌ غير محدد'}")
            print(f"   • BOT_TOKEN: {'✅ محدد' if config.BOT_TOKEN else '❌ غير محدد'}")
        except:
            print("\n⚙️ الإعدادات: ❌ ملف config.py غير موجود")
        
    except Exception as e:
        print(f"❌ خطأ في عرض المعلومات: {e}")

async def run_all_tests():
    """تشغيل جميع الاختبارات"""
    
    print("🚀 مرحباً بك في اختبار Telethon لمشروع ZeMusic!")
    print("=" * 60)
    
    # عرض معلومات Telethon
    get_telethon_info()
    print("\n" + "=" * 60)
    
    # اختبار الاستيراد
    import_success = test_telethon_import()
    
    if not import_success:
        print("\n" + "=" * 60)
        print("❌ فشل اختبار الاستيراد. يرجى تثبيت Telethon أولاً.")
        return False
    
    # اختبار العميل
    client_success = await test_telethon_client()
    
    # اختبار المدير
    manager_success = test_telethon_manager()
    
    print("\n" + "=" * 60)
    
    # النتيجة النهائية
    if import_success and client_success and manager_success:
        print("✅ جميع الاختبارات نجحت! Telethon جاهزة للاستخدام.")
        print("\n🎯 الخطوات التالية:")
        print("   1. تأكد من ضبط API_ID و API_HASH في config.py")
        print("   2. تأكد من ضبط BOT_TOKEN")
        print("   3. قم بتشغيل البوت: python -m ZeMusic")
        return True
    else:
        print("❌ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        print("\n🔧 نصائح لحل المشاكل:")
        print("   • تأكد من تثبيت Telethon: pip install telethon")
        print("   • تأكد من اتصال الإنترنت")
        print("   • تأكد من صحة إعدادات API")
        return False

if __name__ == "__main__":
    try:
        # تشغيل الاختبارات
        success = asyncio.run(run_all_tests())
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ فادح في الاختبار: {e}")
        sys.exit(1)