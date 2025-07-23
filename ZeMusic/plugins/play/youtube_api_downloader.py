"""
نظام تحميل مختلط محسن - YouTube API + yt-dlp
يستخدم YouTube API للبحث والحصول على معلومات الفيديو
ثم يستخدم yt-dlp مع الكوكيز للتحميل الفعلي
"""

import asyncio
import aiohttp
import yt_dlp
import os
import time
import random
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# استيراد الإعدادات
try:
    import config
    YT_API_KEYS = config.YT_API_KEYS
    COOKIES_FILES = config.COOKIES_FILES
except ImportError:
    YT_API_KEYS = []
    COOKIES_FILES = []

from ZeMusic import LOGGER as _LOGGER

# إنشاء logger محلي للوحدة
LOGGER = _LOGGER(__name__)

class YouTubeAPIManager:
    """مدير مفاتيح YouTube API مع تدوير ذكي وإحصائيات تفصيلية"""
    
    def __init__(self):
        self.api_keys = YT_API_KEYS.copy() if YT_API_KEYS else []
        self.current_key_index = 0
        self.key_usage_count = {}
        self.key_errors = {}
        self.key_success_count = {}
        self.last_key_switch = 0
        self.session = None
        
        # إحصائيات مفصلة
        for key in self.api_keys:
            self.key_usage_count[key] = 0
            self.key_errors[key] = 0
            self.key_success_count[key] = 0
    
    async def get_session(self):
        """الحصول على جلسة aiohttp"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
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
            LOGGER.warning(f"🔑 خطأ في المفتاح {current_key[-10:]}... (أخطاء: {self.key_errors[current_key]})")
        
        # التبديل للمفتاح التالي
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.last_key_switch = time.time()
        
        new_key = self.get_current_key()
        LOGGER.info(f"🔄 تم التبديل للمفتاح {new_key[-10:]}... (استخدام: {self.key_usage_count.get(new_key, 0)})")
        return new_key
    
    def record_success(self):
        """تسجيل نجاح استخدام المفتاح"""
        current_key = self.get_current_key()
        if current_key:
            self.key_success_count[current_key] += 1
    
    def get_stats(self):
        """الحصول على إحصائيات المفاتيح"""
        stats = {}
        for key in self.api_keys:
            key_short = key[-10:] + "..."
            stats[key_short] = {
                'usage': self.key_usage_count.get(key, 0),
                'success': self.key_success_count.get(key, 0),
                'errors': self.key_errors.get(key, 0),
                'success_rate': (self.key_success_count.get(key, 0) / max(1, self.key_usage_count.get(key, 1))) * 100
            }
        return stats
    
    async def close(self):
        """إغلاق الجلسة"""
        if self.session:
            await self.session.close()

class HybridYouTubeDownloader:
    """نظام تحميل مختلط محسن - YouTube API + yt-dlp"""
    
    def __init__(self):
        self.api_manager = YouTubeAPIManager()
        self.cookies_files = COOKIES_FILES.copy() if COOKIES_FILES else []
        self.current_cookie_index = 0
        self.download_stats = {
            'total_searches': 0,
            'api_searches': 0,
            'successful_downloads': 0,
            'failed_downloads': 0
        }
    
    async def search_youtube_api(self, query: str, max_results: int = 5) -> Optional[List[Dict]]:
        """البحث في YouTube باستخدام API مع تدوير المفاتيح"""
        api_key = self.api_manager.get_current_key()
        if not api_key:
            LOGGER.warning("⚠️ لا توجد مفاتيح YouTube API متاحة")
            return None
        
        self.api_manager.key_usage_count[api_key] += 1
        self.download_stats['total_searches'] += 1
        
        try:
            session = await self.api_manager.get_session()
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'key': api_key,
                'order': 'relevance',
                'videoDefinition': 'any',
                'videoDuration': 'any'
            }
            
            LOGGER.info(f"🔍 البحث في YouTube API: {query}")
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        video_info = {
                            'id': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                            'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                            'description': item['snippet']['description'][:200],
                            'channel': item['snippet']['channelTitle']
                        }
                        results.append(video_info)
                    
                    self.api_manager.record_success()
                    self.download_stats['api_searches'] += 1
                    LOGGER.info(f"✅ YouTube API نجح: وجد {len(results)} نتيجة")
                    return results
                    
                elif response.status == 403:
                    LOGGER.warning(f"🔑 مفتاح API محظور مؤقتاً: {response.status}")
                    self.api_manager.rotate_key(error_occurred=True)
                    return None
                else:
                    LOGGER.error(f"❌ خطأ في YouTube API: {response.status}")
                    return None
                    
        except Exception as e:
            LOGGER.error(f"❌ خطأ في البحث بـ YouTube API: {e}")
            self.api_manager.rotate_key(error_occurred=True)
            return None
    
    def get_next_cookie_file(self) -> Optional[str]:
        """الحصول على ملف الكوكيز التالي"""
        if not self.cookies_files:
            return None
            
        cookie_file = self.cookies_files[self.current_cookie_index]
        self.current_cookie_index = (self.current_cookie_index + 1) % len(self.cookies_files)
        
        # التحقق من وجود الملف
        if os.path.exists(cookie_file):
            return cookie_file
        return None
    
    async def download_with_ytdlp(self, video_url: str, output_path: str) -> Tuple[bool, Optional[str]]:
        """تحميل الفيديو باستخدام yt-dlp مع الكوكيز"""
        cookie_file = self.get_next_cookie_file()
        
        # إعدادات yt-dlp محسنة
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            'embed_metadata': True,
            'writeinfojson': False,
            'writethumbnail': True,
            'socket_timeout': 30,
            'retries': 3,
        }
        
        # إضافة الكوكيز إذا كانت متاحة
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            LOGGER.info(f"🍪 استخدام ملف الكوكيز: {cookie_file}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                LOGGER.info(f"⬇️ بدء التحميل من: {video_url}")
                await asyncio.get_event_loop().run_in_executor(None, ydl.download, [video_url])
                
                # التحقق من نجاح التحميل
                if os.path.exists(output_path):
                    self.download_stats['successful_downloads'] += 1
                    LOGGER.info(f"✅ تم التحميل بنجاح: {output_path}")
                    return True, output_path
                else:
                    LOGGER.warning(f"⚠️ الملف غير موجود بعد التحميل: {output_path}")
                    return False, None
                    
        except Exception as e:
            self.download_stats['failed_downloads'] += 1
            LOGGER.error(f"❌ فشل التحميل: {e}")
            return False, None
    
    async def hybrid_search_and_download(self, query: str, output_dir: str = "downloads") -> Tuple[bool, Optional[Dict]]:
        """البحث والتحميل المختلط - API للبحث، yt-dlp للتحميل"""
        try:
            # إنشاء مجلد التحميل
            os.makedirs(output_dir, exist_ok=True)
            
            # البحث باستخدام YouTube API
            search_results = await self.search_youtube_api(query, max_results=3)
            if not search_results:
                LOGGER.warning(f"❌ فشل البحث في YouTube API: {query}")
                return False, None
            
            # محاولة تحميل أول نتيجة
            for result in search_results:
                video_id = result['id']
                video_title = result['title']
                video_url = result['url']
                
                # تنظيف اسم الملف
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                output_path = os.path.join(output_dir, f"{video_id}.mp3")
                
                LOGGER.info(f"🎵 محاولة تحميل: {safe_title}")
                
                # التحميل باستخدام yt-dlp
                success, file_path = await self.download_with_ytdlp(video_url, output_path)
                
                if success and file_path:
                    # إرجاع معلومات النجاح
                    return True, {
                        'title': video_title,
                        'video_id': video_id,
                        'url': video_url,
                        'file_path': file_path,
                        'thumbnail': result.get('thumbnail', ''),
                        'channel': result.get('channel', ''),
                        'source': 'hybrid_api_ytdlp'
                    }
                else:
                    LOGGER.warning(f"⚠️ فشل تحميل: {safe_title}")
                    continue
            
            LOGGER.error(f"❌ فشل تحميل جميع النتائج لـ: {query}")
            return False, None
            
        except Exception as e:
            LOGGER.error(f"❌ خطأ في النظام المختلط: {e}")
            return False, None
    
    def get_download_stats(self) -> Dict:
        """الحصول على إحصائيات التحميل"""
        api_stats = self.api_manager.get_stats()
        return {
            'download_stats': self.download_stats,
            'api_keys_stats': api_stats,
            'cookies_count': len(self.cookies_files),
            'current_cookie': self.current_cookie_index
        }
    
    async def close(self):
        """إغلاق الموارد"""
        await self.api_manager.close()

# إنشاء مثيل عام للاستخدام
hybrid_downloader = HybridYouTubeDownloader()

async def search_youtube_hybrid(query: str) -> Optional[List[Dict]]:
    """البحث المختلط في YouTube"""
    return await hybrid_downloader.search_youtube_api(query)

async def download_youtube_hybrid(query: str, output_dir: str = "downloads") -> Tuple[bool, Optional[Dict]]:
    """تحميل مختلط من YouTube"""
    return await hybrid_downloader.hybrid_search_and_download(query, output_dir)

async def get_hybrid_stats() -> Dict:
    """الحصول على إحصائيات النظام المختلط"""
    return hybrid_downloader.get_download_stats()