#!/usr/bin/env python3
"""
ملف تجريبي لاختبار استخدام مفاتيح YouTube API
"""

import asyncio
import aiohttp
import json
import random
import time
import sys
import os

# إضافة مسار المشروع
sys.path.append('/workspace')

try:
    import config
    YT_API_KEYS = config.YT_API_KEYS
except ImportError:
    # مفاتيح افتراضية للاختبار
    YT_API_KEYS = [
        "AIzaSyA3x5N5DNYzd5j7L7JMn9XsUYil32Ak77U",
        "AIzaSyDw09GqGziUHXZ3FjugOypSXD7tedWzIzQ"
    ]

class YouTubeAPIManager:
    """مدير مفاتيح YouTube API مع تدوير ذكي"""
    
    def __init__(self):
        self.api_keys = YT_API_KEYS.copy()
        self.current_key_index = 0
        self.key_usage_count = {}
        self.key_errors = {}
        self.last_key_switch = 0
        
        # إحصائيات الاستخدام
        for key in self.api_keys:
            self.key_usage_count[key] = 0
            self.key_errors[key] = 0
    
    def get_current_key(self):
        """الحصول على المفتاح الحالي"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]
    
    def rotate_key(self, error_occurred=False):
        """تدوير المفاتيح مع تسجيل الأخطاء"""
        if not self.api_keys:
            return None
            
        current_key = self.get_current_key()
        
        if error_occurred and current_key:
            self.key_errors[current_key] += 1
            print(f"⚠️ خطأ في المفتاح: {current_key[:10]}... (أخطاء: {self.key_errors[current_key]})")
        
        # الانتقال للمفتاح التالي
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.last_key_switch = time.time()
        
        new_key = self.get_current_key()
        print(f"🔄 تم التبديل للمفتاح: {new_key[:10]}...")
        return new_key
    
    def get_best_key(self):
        """الحصول على أفضل مفتاح (أقل أخطاء)"""
        if not self.api_keys:
            return None
            
        # ترتيب المفاتيح حسب عدد الأخطاء
        sorted_keys = sorted(self.api_keys, key=lambda k: self.key_errors[k])
        best_key = sorted_keys[0]
        
        # تحديث المؤشر
        self.current_key_index = self.api_keys.index(best_key)
        return best_key
    
    def mark_key_used(self, key):
        """تسجيل استخدام المفتاح"""
        if key in self.key_usage_count:
            self.key_usage_count[key] += 1
    
    def get_stats(self):
        """إحصائيات المفاتيح"""
        stats = {
            'total_keys': len(self.api_keys),
            'current_key': self.get_current_key()[:10] + "..." if self.get_current_key() else "None",
            'usage_stats': {},
            'error_stats': {}
        }
        
        for key in self.api_keys:
            key_short = key[:10] + "..."
            stats['usage_stats'][key_short] = self.key_usage_count[key]
            stats['error_stats'][key_short] = self.key_errors[key]
        
        return stats

class YouTubeAPIDownloader:
    """محمل باستخدام YouTube API"""
    
    def __init__(self):
        self.api_manager = YouTubeAPIManager()
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_youtube(self, query, max_results=5):
        """البحث في YouTube باستخدام API"""
        api_key = self.api_manager.get_current_key()
        if not api_key:
            print("❌ لا توجد مفاتيح API متاحة")
            return None
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': api_key
        }
        
        try:
            print(f"🔍 البحث باستخدام المفتاح: {api_key[:10]}...")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_manager.mark_key_used(api_key)
                    return data
                elif response.status == 403:
                    # المفتاح محظور أو منتهي الصلاحية
                    print(f"❌ المفتاح محظور: {response.status}")
                    self.api_manager.rotate_key(error_occurred=True)
                    # إعادة المحاولة مع مفتاح جديد
                    return await self.search_youtube(query, max_results)
                else:
                    print(f"❌ خطأ في API: {response.status}")
                    error_text = await response.text()
                    print(f"تفاصيل الخطأ: {error_text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"❌ خطأ في الاتصال: {e}")
            self.api_manager.rotate_key(error_occurred=True)
            return None
    
    async def get_video_details(self, video_id):
        """الحصول على تفاصيل الفيديو"""
        api_key = self.api_manager.get_current_key()
        if not api_key:
            return None
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_manager.mark_key_used(api_key)
                    return data
                else:
                    print(f"❌ خطأ في الحصول على تفاصيل الفيديو: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ خطأ في الاتصال: {e}")
            return None

async def test_youtube_api():
    """اختبار مفاتيح YouTube API"""
    print("🚀 اختبار مفاتيح YouTube API")
    print("=" * 50)
    
    # عرض المفاتيح المتاحة
    print(f"📊 عدد المفاتيح المتاحة: {len(YT_API_KEYS)}")
    for i, key in enumerate(YT_API_KEYS):
        print(f"   {i+1}. {key[:15]}...")
    print()
    
    async with YouTubeAPIDownloader() as downloader:
        # اختبار البحث
        test_queries = [
            "أصيل أبو بكر",
            "محمد عبده",
            "فيروز",
            "عمرو دياب"
        ]
        
        for query in test_queries:
            print(f"🔍 اختبار البحث: '{query}'")
            results = await downloader.search_youtube(query, max_results=3)
            
            if results and 'items' in results:
                print(f"✅ تم العثور على {len(results['items'])} نتيجة")
                for item in results['items']:
                    title = item['snippet']['title']
                    video_id = item['id']['videoId']
                    channel = item['snippet']['channelTitle']
                    print(f"   📹 {title[:50]}... | {channel}")
                    
                    # اختبار تفاصيل الفيديو
                    details = await downloader.get_video_details(video_id)
                    if details and 'items' in details and details['items']:
                        duration = details['items'][0]['contentDetails']['duration']
                        views = details['items'][0]['statistics'].get('viewCount', 'N/A')
                        print(f"      ⏱️ المدة: {duration} | 👁️ مشاهدات: {views}")
                    
                    break  # فقط أول نتيجة للاختبار
            else:
                print("❌ لم يتم العثور على نتائج")
            
            print()
            
            # انتظار قصير بين الطلبات
            await asyncio.sleep(1)
        
        # عرض الإحصائيات
        stats = downloader.api_manager.get_stats()
        print("📊 إحصائيات المفاتيح:")
        print(f"   إجمالي المفاتيح: {stats['total_keys']}")
        print(f"   المفتاح الحالي: {stats['current_key']}")
        print("   إحصائيات الاستخدام:")
        for key, count in stats['usage_stats'].items():
            errors = stats['error_stats'][key]
            print(f"      {key}: {count} استخدام، {errors} خطأ")

async def test_hybrid_download(query):
    """اختبار التحميل المختلط (API + yt-dlp)"""
    print(f"🔄 اختبار التحميل المختلط: '{query}'")
    print("=" * 50)
    
    async with YouTubeAPIDownloader() as downloader:
        # البحث باستخدام API
        results = await downloader.search_youtube(query, max_results=1)
        
        if results and 'items' in results:
            video_id = results['items'][0]['id']['videoId']
            title = results['items'][0]['snippet']['title']
            
            print(f"✅ تم العثور على: {title}")
            print(f"🆔 معرف الفيديو: {video_id}")
            
            # محاولة التحميل باستخدام yt-dlp
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"🔗 رابط الفيديو: {video_url}")
            
            # هنا يمكن إضافة كود yt-dlp للتحميل الفعلي
            print("💡 يمكن الآن استخدام yt-dlp للتحميل من هذا الرابط")
            
            return {
                'video_id': video_id,
                'title': title,
                'url': video_url,
                'api_success': True
            }
        else:
            print("❌ فشل البحث باستخدام API")
            return {'api_success': False}

if __name__ == "__main__":
    print("🎵 اختبار نظام YouTube API للبوت الموسيقي")
    print("=" * 60)
    
    # اختبار المفاتيح
    asyncio.run(test_youtube_api())
    
    print("\n" + "=" * 60)
    
    # اختبار التحميل المختلط
    asyncio.run(test_hybrid_download("أصيل أبو بكر"))