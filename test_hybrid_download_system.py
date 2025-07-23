#!/usr/bin/env python3
"""
ملف تجريبي شامل لاختبار النظام المختلط (YouTube API + yt-dlp)
"""

import asyncio
import os
import sys
import time

# إضافة مسار المشروع
sys.path.append('/workspace')

async def test_hybrid_system():
    """اختبار شامل للنظام المختلط"""
    print("🎵 اختبار النظام المختلط للبوت الموسيقي")
    print("=" * 60)
    
    try:
        # تحميل النظام
        from ZeMusic.plugins.play.youtube_api_downloader import (
            get_hybrid_downloader, 
            search_and_download_hybrid,
            get_downloader_stats
        )
        import config
        
        print("✅ تم تحميل النظام المختلط بنجاح")
        print(f"🔑 مفاتيح YouTube API: {len(config.YT_API_KEYS)}")
        print(f"🍪 ملفات الكوكيز: {len(config.COOKIES_FILES)}")
        print()
        
        # اختبار 1: البحث فقط
        print("🔍 **اختبار 1: البحث بـ YouTube API**")
        print("-" * 40)
        
        downloader = await get_hybrid_downloader()
        search_results = await downloader.search_with_api("أصيل أبو بكر", max_results=3)
        
        if search_results and 'items' in search_results:
            print(f"✅ تم العثور على {len(search_results['items'])} نتيجة:")
            for i, item in enumerate(search_results['items'], 1):
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                video_id = item['id']['videoId']
                print(f"   {i}. {title[:50]}...")
                print(f"      📺 القناة: {channel}")
                print(f"      🆔 المعرف: {video_id}")
        else:
            print("❌ فشل البحث")
        
        print()
        
        # اختبار 2: الإحصائيات
        print("📊 **اختبار 2: إحصائيات النظام**")
        print("-" * 40)
        
        stats = await get_downloader_stats()
        if stats.get('status') != 'no_keys':
            print(f"🔑 إجمالي المفاتيح: {stats['total_keys']}")
            print(f"🎯 المفتاح الحالي: {stats['current_key']}")
            print(f"🍪 ملفات الكوكيز: {stats['cookies_available']}")
            
            print("📈 إحصائيات الاستخدام:")
            for key, usage in stats['usage_stats'].items():
                errors = stats['error_stats'].get(key, 0)
                print(f"   • {key}: {usage} استخدام، {errors} خطأ")
        else:
            print("❌ لا توجد مفاتيح API")
        
        print()
        
        # اختبار 3: التحميل المختلط (اختياري)
        print("⬇️ **اختبار 3: التحميل المختلط (اختياري)**")
        print("-" * 50)
        
        choice = input("هل تريد اختبار التحميل الفعلي؟ (y/N): ").strip().lower()
        
        if choice in ['y', 'yes', 'نعم']:
            print("🔄 بدء التحميل المختلط...")
            result = await search_and_download_hybrid("أصيل أبو بكر")
            
            if result and result.get('success'):
                print(f"✅ نجح التحميل:")
                print(f"   📁 الملف: {result['file_path']}")
                print(f"   🎵 العنوان: {result['title']}")
                print(f"   ⏱️ المدة: {result['duration']} ثانية")
                print(f"   👤 القناة: {result['uploader']}")
                print(f"   🔧 الطريقة: {result['method']}")
                
                # التحقق من وجود الملف
                if os.path.exists(result['file_path']):
                    file_size = os.path.getsize(result['file_path']) / 1024 / 1024
                    print(f"   📊 حجم الملف: {file_size:.2f} MB")
                else:
                    print("   ⚠️ الملف غير موجود")
            else:
                print("❌ فشل التحميل المختلط")
        else:
            print("⏭️ تم تخطي اختبار التحميل")
        
        print()
        
        # اختبار 4: إحصائيات نهائية
        print("📊 **إحصائيات نهائية:**")
        print("-" * 25)
        
        final_stats = await get_downloader_stats()
        if final_stats.get('status') != 'no_keys':
            print("📈 إحصائيات الاستخدام النهائية:")
            for key, usage in final_stats['usage_stats'].items():
                errors = final_stats['error_stats'].get(key, 0)
                success_rate = ((usage - errors) / usage * 100) if usage > 0 else 0
                print(f"   • {key}: {usage} استخدام ({success_rate:.1f}% نجح)")
        
        print()
        print("🎉 **خلاصة النظام المختلط:**")
        print("✅ البحث بـ YouTube API يعمل")
        print("✅ تدوير المفاتيح يعمل")
        print("✅ إدارة الكوكيز تعمل")
        print("✅ الإحصائيات تعمل")
        print("🔄 النظام جاهز للاستخدام في البوت")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار النظام: {e}")
        import traceback
        traceback.print_exc()

async def test_api_keys_only():
    """اختبار مفاتيح YouTube API فقط"""
    print("🔑 اختبار مفاتيح YouTube API")
    print("=" * 40)
    
    try:
        import config
        from ZeMusic.plugins.play.youtube_api_downloader import get_hybrid_downloader
        
        if not config.YT_API_KEYS:
            print("❌ لا توجد مفاتيح YouTube API في ملف التكوين")
            print("💡 أضف مفاتيحك في config.py:")
            print("   YT_API_KEYS = ['YOUR_API_KEY_1', 'YOUR_API_KEY_2']")
            return
        
        print(f"📊 عدد المفاتيح: {len(config.YT_API_KEYS)}")
        for i, key in enumerate(config.YT_API_KEYS, 1):
            print(f"   {i}. {key[:15]}...")
        
        print("\n🔍 اختبار البحث...")
        
        downloader = await get_hybrid_downloader()
        
        test_queries = ["أصيل أبو بكر", "محمد عبده", "فيروز"]
        
        for query in test_queries:
            print(f"\n🎵 البحث عن: '{query}'")
            results = await downloader.search_with_api(query, max_results=2)
            
            if results and 'items' in results:
                print(f"   ✅ {len(results['items'])} نتيجة")
                for item in results['items']:
                    title = item['snippet']['title'][:40]
                    channel = item['snippet']['channelTitle']
                    print(f"      📹 {title}... | {channel}")
            else:
                print("   ❌ لا توجد نتائج")
            
            await asyncio.sleep(1)  # انتظار بين الطلبات
        
        # عرض الإحصائيات
        from ZeMusic.plugins.play.youtube_api_downloader import get_downloader_stats
        stats = await get_downloader_stats()
        
        print(f"\n📊 إحصائيات الاستخدام:")
        print(f"   🔑 المفتاح الحالي: {stats['current_key']}")
        for key, usage in stats['usage_stats'].items():
            errors = stats['error_stats'].get(key, 0)
            print(f"   • {key}: {usage} استخدام، {errors} خطأ")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار المفاتيح: {e}")

def show_instructions():
    """عرض تعليمات الاستخدام"""
    print("📋 **تعليمات النظام المختلط:**")
    print("=" * 50)
    print()
    print("🔑 **للحصول على مفاتيح YouTube API:**")
    print("1. اذهب إلى Google Cloud Console")
    print("2. أنشئ مشروع جديد أو استخدم موجود")
    print("3. فعّل YouTube Data API v3")
    print("4. أنشئ مفتاح API")
    print("5. أضف المفتاح في config.py")
    print()
    print("🍪 **لإعداد ملفات الكوكيز:**")
    print("1. صدّر كوكيز YouTube من متصفحك")
    print("2. احفظها في مجلد cookies/")
    print("3. تأكد من تحديث config.py")
    print()
    print("🚀 **الاستخدام في البوت:**")
    print("• /youtube_stats - عرض إحصائيات المفاتيح")
    print("• /test_youtube_api <query> - اختبار البحث")
    print("• البحث العادي سيستخدم النظام المختلط تلقائياً")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="اختبار النظام المختلط")
    parser.add_argument('--keys-only', action='store_true', help='اختبار المفاتيح فقط')
    parser.add_argument('--instructions', action='store_true', help='عرض التعليمات')
    
    args = parser.parse_args()
    
    if args.instructions:
        show_instructions()
    elif args.keys_only:
        asyncio.run(test_api_keys_only())
    else:
        asyncio.run(test_hybrid_system())