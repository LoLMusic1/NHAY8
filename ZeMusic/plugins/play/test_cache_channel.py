# -*- coding: utf-8 -*-
"""
🧪 اختبار قناة التخزين الذكي
========================

اختبار اتصال وإعدادات قناة التخزين
"""

import asyncio
import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER
from ZeMusic.plugins.play.download_enhanced import SMART_CACHE_CHANNEL

async def test_cache_channel_connection():
    """اختبار الاتصال بقناة التخزين"""
    
    LOGGER(__name__).info("🧪 بدء اختبار قناة التخزين...")
    
    # فحص إعدادات القناة
    print(f"📺 قناة التخزين المحددة: {SMART_CACHE_CHANNEL}")
    
    if not SMART_CACHE_CHANNEL:
        print("❌ قناة التخزين غير محددة!")
        print("💡 تأكد من إعداد CACHE_CHANNEL_USERNAME في ملف .env")
        return False
    
    try:
        # اختبار الحصول على معلومات القناة
        entity = await telethon_manager.bot_client.get_entity(SMART_CACHE_CHANNEL)
        
        print(f"✅ تم الاتصال بالقناة بنجاح!")
        print(f"📝 اسم القناة: {entity.title}")
        print(f"👥 عدد الأعضاء: {getattr(entity, 'participants_count', 'غير معروف')}")
        print(f"📋 الوصف: {entity.about[:100] if hasattr(entity, 'about') and entity.about else 'لا يوجد'}")
        
        # اختبار إرسال رسالة تجريبية
        test_message = await telethon_manager.bot_client.send_message(
            entity=SMART_CACHE_CHANNEL,
            message="🧪 **اختبار قناة التخزين الذكي**\n\n✅ البوت متصل بالقناة بنجاح!\n🎵 يمكن الآن حفظ الملفات الصوتية هنا تلقائياً."
        )
        
        print(f"📨 تم إرسال رسالة اختبار: {test_message.id}")
        
        # حذف الرسالة بعد 30 ثانية
        await asyncio.sleep(5)
        try:
            await test_message.delete()
            print("🗑️ تم حذف رسالة الاختبار")
        except:
            print("⚠️ لم يتم حذف رسالة الاختبار (ربما لا توجد صلاحيات)")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل الاتصال بقناة التخزين!")
        print(f"🚫 الخطأ: {str(e)}")
        print(f"\n💡 تأكد من:")
        print(f"• البوت أدمن في القناة @{SMART_CACHE_CHANNEL}")
        print(f"• صحة يوزر القناة")
        print(f"• تفعيل إرسال الرسائل للبوت")
        
        return False

async def test_cache_download_and_save():
    """اختبار تحميل وحفظ ملف في قناة التخزين"""
    
    if not SMART_CACHE_CHANNEL:
        print("❌ قناة التخزين غير محددة - تجاهل اختبار الحفظ")
        return False
    
    try:
        from ZeMusic.plugins.play.download_enhanced import downloader
        
        print("🔍 اختبار تحميل أغنية وحفظها في قناة التخزين...")
        
        # تجربة البحث والتحميل
        test_query = "test song"
        result = await downloader.hyper_download(test_query, "low")  # جودة منخفضة للاختبار
        
        if result:
            if result.get('cached'):
                print("⚡ تم الحصول على النتيجة من الكاش - لا حاجة لحفظ جديد")
            else:
                print("✅ تم التحميل بنجاح وحفظه في قناة التخزين!")
                print(f"🎵 العنوان: {result.get('title', 'غير معروف')}")
                print(f"🎤 الفنان: {result.get('artist', 'غير معروف')}")
        else:
            print("❌ فشل التحميل - لا يمكن اختبار الحفظ")
            
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التحميل والحفظ: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 بدء اختبار شامل لقناة التخزين الذكي\n")
        
        # الاختبار الأول: الاتصال
        connection_test = await test_cache_channel_connection()
        
        print("\n" + "="*50 + "\n")
        
        # الاختبار الثاني: التحميل والحفظ
        if connection_test:
            download_test = await test_cache_download_and_save()
        else:
            print("⏭️ تجاهل اختبار التحميل بسبب فشل الاتصال")
        
        print("\n🏁 انتهى الاختبار")
    
    # تشغيل الاختبار
    asyncio.run(main())