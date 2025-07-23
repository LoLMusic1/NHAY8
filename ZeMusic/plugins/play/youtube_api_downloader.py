"""
نظام تحميل مختلط يستخدم YouTube API مع yt-dlp
يدمج البحث بالمفاتيح والتحميل بالكوكيز
"""

import asyncio
import aiohttp
import yt_dlp
import os
import time
import random
from pathlib import Path
from typing import Optional, Dict, List

# استيراد الإعدادات
try:
    import config
    YT_API_KEYS = config.YT_API_KEYS
    COOKIES_FILES = config.COOKIES_FILES
except ImportError:
    YT_API_KEYS = []
    COOKIES_FILES = []

from ZeMusic import LOGGER

class YouTubeAPIManager:
    """مدير مفاتيح YouTube API مع تدوير ذكي"""
    
    def __init__(self):
        self.api_keys = YT_API_KEYS.copy() if YT_API_KEYS else []
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
            LOGGER(__name__).warning(f"⚠️ خطأ في مفتاح API: {current_key[:10]}... (أخطاء: {self.key_errors[current_key]})")
        
        # الانتقال للمفتاح التالي
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.last_key_switch = time.time()
        
        new_key = self.get_current_key()
        LOGGER(__name__).info(f"🔄 تم التبديل لمفتاح API جديد: {new_key[:10]}...")
        return new_key
    
    def mark_key_used(self, key):
        """تسجيل استخدام المفتاح"""
        if key in self.key_usage_count:
            self.key_usage_count[key] += 1

class HybridYouTubeDownloader:
    """محمل مختلط يستخدم YouTube API + yt-dlp"""
    
    def __init__(self):
        self.api_manager = YouTubeAPIManager()
        self.session = None
        self.cookies_files = COOKIES_FILES.copy() if COOKIES_FILES else []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_with_api(self, query: str, max_results: int = 5) -> Optional[Dict]:
        """البحث باستخدام YouTube API"""
        api_key = self.api_manager.get_current_key()
        if not api_key:
            LOGGER(__name__).warning("⚠️ لا توجد مفاتيح YouTube API متاحة")
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
            LOGGER(__name__).info(f"🔍 البحث بـ YouTube API: {query}")
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_manager.mark_key_used(api_key)
                    LOGGER(__name__).info(f"✅ API نجح: {len(data.get('items', []))} نتيجة")
                    return data
                elif response.status == 403:
                    # المفتاح محظور أو منتهي الصلاحية
                    LOGGER(__name__).warning(f"❌ مفتاح API محظور: {response.status}")
                    self.api_manager.rotate_key(error_occurred=True)
                    # إعادة المحاولة مع مفتاح جديد
                    if len(self.api_manager.api_keys) > 1:
                        return await self.search_with_api(query, max_results)
                    return None
                else:
                    LOGGER(__name__).error(f"❌ خطأ في YouTube API: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            LOGGER(__name__).warning("⏰ انتهت مهلة YouTube API")
            return None
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في الاتصال بـ YouTube API: {e}")
            self.api_manager.rotate_key(error_occurred=True)
            return None
    
    def get_best_cookie_file(self) -> Optional[str]:
        """الحصول على أفضل ملف كوكيز متاح"""
        if not self.cookies_files:
            return None
        
        # فلترة الملفات الموجودة
        available_cookies = [f for f in self.cookies_files if os.path.exists(f)]
        if not available_cookies:
            return None
        
        # اختيار عشوائي لتوزيع الحمولة
        return random.choice(available_cookies)
    
    async def download_with_ytdlp(self, video_id: str, title: str = "") -> Optional[Dict]:
        """التحميل باستخدام yt-dlp مع الكوكيز"""
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        cookie_file = self.get_best_cookie_file()
        
        # إعدادات yt-dlp محسنة
        ydl_opts = {
            'format': 'bestaudio[filesize<25M]/best[filesize<25M]',
            'outtmpl': str(downloads_dir / f'{video_id}_hybrid.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 20,
            'retries': 2,
            'concurrent_fragment_downloads': 2,
            'http_chunk_size': 4194304,  # 4MB chunks
            'prefer_ffmpeg': True,
        }
        
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            LOGGER(__name__).info(f"🍪 استخدام كوكيز: {os.path.basename(cookie_file)}")
        
        try:
            LOGGER(__name__).info(f"⬇️ بدء التحميل المختلط: {title[:50]}...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                if info:
                    # البحث عن الملف المحمل
                    for file_path in downloads_dir.glob(f"{video_id}_hybrid.*"):
                        if file_path.suffix in ['.m4a', '.mp3', '.webm', '.mp4', '.opus']:
                            LOGGER(__name__).info(f"✅ تم التحميل المختلط بنجاح")
                            return {
                                'success': True,
                                'file_path': str(file_path),
                                'title': info.get('title', title),
                                'duration': info.get('duration', 0),
                                'uploader': info.get('uploader', 'Unknown'),
                                'video_id': video_id,
                                'method': 'hybrid_api_ytdlp'
                            }
            
            LOGGER(__name__).warning("⚠️ لم يتم العثور على ملف محمل")
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في التحميل المختلط: {e}")
            return None
    
    async def hybrid_search_and_download(self, query: str) -> Optional[Dict]:
        """البحث والتحميل المختلط (API + yt-dlp)"""
        try:
            # الخطوة 1: البحث باستخدام YouTube API
            search_results = await self.search_with_api(query, max_results=3)
            
            if search_results and 'items' in search_results:
                # جرب تحميل أول نتيجة
                for item in search_results['items']:
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    
                    LOGGER(__name__).info(f"🎯 محاولة تحميل: {title[:50]}... | {channel}")
                    
                    # الخطوة 2: التحميل باستخدام yt-dlp
                    download_result = await self.download_with_ytdlp(video_id, title)
                    
                    if download_result and download_result['success']:
                        # إضافة معلومات من API
                        download_result.update({
                            'channel': channel,
                            'description': item['snippet'].get('description', ''),
                            'published_at': item['snippet'].get('publishedAt', ''),
                            'api_enhanced': True
                        })
                        return download_result
                    else:
                        LOGGER(__name__).warning(f"⚠️ فشل تحميل: {title[:30]}...")
                        continue
            
            LOGGER(__name__).warning("❌ فشل البحث والتحميل المختلط")
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في العملية المختلطة: {e}")
            return None
    
    def get_api_stats(self) -> Dict:
        """إحصائيات استخدام المفاتيح"""
        if not self.api_manager.api_keys:
            return {'status': 'no_keys'}
        
        stats = {
            'total_keys': len(self.api_manager.api_keys),
            'current_key': self.api_manager.get_current_key()[:10] + "..." if self.api_manager.get_current_key() else "None",
            'usage_stats': {},
            'error_stats': {},
            'cookies_available': len(self.cookies_files)
        }
        
        for key in self.api_manager.api_keys:
            key_short = key[:10] + "..."
            stats['usage_stats'][key_short] = self.api_manager.key_usage_count[key]
            stats['error_stats'][key_short] = self.api_manager.key_errors[key]
        
        return stats

# إنشاء مثيل عام للاستخدام
hybrid_downloader = None

async def get_hybrid_downloader():
    """الحصول على محمل مختلط"""
    global hybrid_downloader
    if hybrid_downloader is None:
        hybrid_downloader = HybridYouTubeDownloader()
        await hybrid_downloader.__aenter__()
    return hybrid_downloader

async def search_and_download_hybrid(query: str) -> Optional[Dict]:
    """وظيفة سهلة للبحث والتحميل المختلط"""
    downloader = await get_hybrid_downloader()
    return await downloader.hybrid_search_and_download(query)

async def get_downloader_stats() -> Dict:
    """الحصول على إحصائيات المحمل"""
    if hybrid_downloader:
        return hybrid_downloader.get_api_stats()
    return {'status': 'not_initialized'}