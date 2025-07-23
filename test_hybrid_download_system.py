#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل للنظام المختلط المحسن
YouTube API Keys + yt-dlp + Cookies
"""

import asyncio
import os
import time
from pathlib import Path

async def test_hybrid_system():
    """اختبار شامل للنظام المختلط"""
    
    print("🧪 بدء اختبار النظام المختلط المحسن")
    print("=" * 50)
    
    try:
        # استيراد النظام المختلط
        from ZeMusic.plugins.play.youtube_api_downloader import (
            hybrid_downloader,
            search_youtube_hybrid,
            download_youtube_hybrid,
            get_hybrid_stats
        )
        
        print("✅ تم استيراد النظام المختلط بنجاح")
        
        # اختبار 1: عرض الإحصائيات الأولية
        print("\n📊 الإحصائيات الأولية:")
        stats = await get_hybrid_stats()
        print(f"   🔑 عدد مفاتيح API: {len(stats.get('api_keys_stats', {}))}")
        print(f"   🍪 عدد ملفات الكوكيز: {stats.get('cookies_count', 0)}")
        print(f"   📈 إجمالي البحث: {stats['download_stats']['total_searches']}")
        
        # اختبار 2: البحث بـ YouTube API
        print("\n🔍 اختبار البحث بـ YouTube API:")
        search_query = "أصيل أبو بكر"
        print(f"   البحث عن: {search_query}")
        
        search_results = await search_youtube_hybrid(search_query)
        if search_results:
            print(f"   ✅ تم العثور على {len(search_results)} نتيجة")
            for i, result in enumerate(search_results[:2], 1):
                print(f"   {i}. {result['title'][:50]}...")
                print(f"      📺 القناة: {result['channel']}")
                print(f"      🆔 المعرف: {result['id']}")
        else:
            print("   ❌ فشل البحث")
        
        # اختبار 3: التحميل المختلط
        print("\n⬇️ اختبار التحميل المختلط:")
        download_query = "محمد عبده قريب"
        print(f"   التحميل: {download_query}")
        
        start_time = time.time()
        success, result = await download_youtube_hybrid(download_query, "test_downloads")
        elapsed = time.time() - start_time
        
        if success and result:
            print(f"   ✅ نجح التحميل في {elapsed:.2f} ثانية")
            print(f"   🎵 العنوان: {result['title'][:50]}...")
            print(f"   📁 الملف: {result['file_path']}")
            print(f"   📺 القناة: {result.get('channel', 'غير محدد')}")
            print(f"   🔗 الرابط: {result['url']}")
            
            # التحقق من وجود الملف
            if os.path.exists(result['file_path']):
                file_size = os.path.getsize(result['file_path'])
                print(f"   📊 حجم الملف: {file_size / 1024 / 1024:.2f} MB")
            else:
                print("   ⚠️ الملف غير موجود")
        else:
            print(f"   ❌ فشل التحميل في {elapsed:.2f} ثانية")
        
        # اختبار 4: الإحصائيات النهائية
        print("\n📊 الإحصائيات النهائية:")
        final_stats = await get_hybrid_stats()
        
        print("   🔑 إحصائيات مفاتيح API:")
        for key, stats in final_stats.get('api_keys_stats', {}).items():
            print(f"      {key}: استخدام={stats['usage']}, نجاح={stats['success']}, أخطاء={stats['errors']}")
        
        print("   📈 إحصائيات التحميل:")
        dl_stats = final_stats['download_stats']
        print(f"      إجمالي البحث: {dl_stats['total_searches']}")
        print(f"      بحث API: {dl_stats['api_searches']}")
        print(f"      تحميل ناجح: {dl_stats['successful_downloads']}")
        print(f"      تحميل فاشل: {dl_stats['failed_downloads']}")
        
        # اختبار 5: تنظيف الملفات التجريبية
        print("\n🧹 تنظيف الملفات التجريبية:")
        test_dir = Path("test_downloads")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            print("   ✅ تم حذف مجلد الاختبار")
        
        print("\n🎉 انتهى اختبار النظام المختلط بنجاح!")
        
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        print("تأكد من أن البوت يعمل ومن وجود الملفات المطلوبة")
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

async def test_api_keys_rotation():
    """اختبار تدوير مفاتيح API"""
    print("\n🔄 اختبار تدوير مفاتيح API:")
    
    try:
        from ZeMusic.plugins.play.youtube_api_downloader import hybrid_downloader
        
        api_manager = hybrid_downloader.api_manager
        print(f"   عدد المفاتيح: {len(api_manager.api_keys)}")
        
        if api_manager.api_keys:
            current_key = api_manager.get_current_key()
            print(f"   المفتاح الحالي: ...{current_key[-10:] if current_key else 'لا يوجد'}")
            
            # تجربة التدوير
            for i in range(3):
                new_key = api_manager.rotate_key()
                print(f"   تدوير {i+1}: ...{new_key[-10:] if new_key else 'لا يوجد'}")
        else:
            print("   ⚠️ لا توجد مفاتيح API")
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار التدوير: {e}")

if __name__ == "__main__":
    print("🎯 اختبار النظام المختلط المحسن")
    print("YouTube API Keys + yt-dlp + Cookies")
    print("=" * 60)
    
    # تشغيل الاختبارات
    asyncio.run(test_hybrid_system())
    asyncio.run(test_api_keys_rotation())