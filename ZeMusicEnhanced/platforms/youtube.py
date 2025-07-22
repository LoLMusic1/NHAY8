#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced YouTube Platform
تاريخ الإنشاء: 2025-01-28

منصة YouTube المحسنة مع دعم yt-dlp
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from .platform_manager import BasePlatform
from ..config import config

logger = logging.getLogger(__name__)

class YouTubePlatform(BasePlatform):
    """منصة YouTube"""
    
    def __init__(self):
        super().__init__("YouTube")
        self.ydl = None
        self.search_limit = 10
    
    async def initialize(self) -> bool:
        """تهيئة منصة YouTube"""
        try:
            if not YT_DLP_AVAILABLE:
                logger.error("❌ yt-dlp غير متاح - لن تعمل منصة YouTube")
                return False
            
            # إعدادات yt-dlp
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'noplaylist': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': f"{config.music.temp_path}/%(title)s.%(ext)s",
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'socket_timeout': 30,
                'retries': 3
            }
            
            # إضافة cookie file إذا كان متاحاً
            if config.music.youtube_cookies_path:
                ydl_opts['cookiefile'] = config.music.youtube_cookies_path
            
            self.ydl = yt_dlp.YoutubeDL(ydl_opts)
            self.is_available = True
            
            logger.info("✅ تم تهيئة منصة YouTube بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة منصة YouTube: {e}")
            return False
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """البحث في YouTube"""
        try:
            if not self.is_available:
                return []
            
            # تنظيف استعلام البحث
            clean_query = self._clean_search_query(query)
            
            # تشغيل البحث في thread منفصل
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._search_youtube, 
                clean_query, 
                limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ فشل البحث في YouTube: {e}")
            return []
    
    def _search_youtube(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """البحث الفعلي في YouTube"""
        try:
            search_query = f"ytsearch{limit}:{query}"
            
            # استخراج معلومات البحث
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                search_results = ydl.extract_info(
                    search_query,
                    download=False,
                    process=False
                )
            
            results = []
            
            if search_results and 'entries' in search_results:
                for entry in search_results['entries']:
                    if entry:
                        result = self._format_youtube_result(entry)
                        if result:
                            results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث الفعلي في YouTube: {e}")
            return []
    
    def _format_youtube_result(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """تنسيق نتيجة البحث من YouTube"""
        try:
            # التحقق من البيانات الأساسية
            if not entry.get('id') or not entry.get('title'):
                return None
            
            # فلترة المحتوى غير المرغوب
            title = entry.get('title', '').lower()
            if any(keyword in title for keyword in ['live', 'stream', 'news', 'talk']):
                # تخطي البثوث المباشرة والأخبار
                if entry.get('duration', 0) > 3600:  # أكثر من ساعة
                    return None
            
            # استخراج معلومات المقطع
            result = {
                'id': entry['id'],
                'title': entry.get('title', 'عنوان غير معروف'),
                'url': f"https://www.youtube.com/watch?v={entry['id']}",
                'duration': entry.get('duration', 0),
                'thumbnail': self._get_best_thumbnail(entry.get('thumbnails', [])),
                'uploader': entry.get('uploader', 'قناة غير معروفة'),
                'view_count': entry.get('view_count', 0),
                'upload_date': entry.get('upload_date', ''),
                'description': entry.get('description', '')[:200] + '...' if entry.get('description') else '',
                'quality': self._determine_quality(entry),
                'platform': 'youtube',
                'platform_display': 'YouTube'
            }
            
            # إضافة معلومات إضافية
            result['artist'] = self._extract_artist(result['title'], result['uploader'])
            result['views'] = result['view_count']
            
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنسيق نتيجة YouTube: {e}")
            return None
    
    def _get_best_thumbnail(self, thumbnails: List[Dict[str, Any]]) -> str:
        """الحصول على أفضل صورة مصغرة"""
        try:
            if not thumbnails:
                return ""
            
            # ترتيب الصور حسب الجودة
            sorted_thumbs = sorted(
                thumbnails, 
                key=lambda x: x.get('width', 0) * x.get('height', 0), 
                reverse=True
            )
            
            return sorted_thumbs[0].get('url', '') if sorted_thumbs else ""
            
        except Exception:
            return ""
    
    def _determine_quality(self, entry: Dict[str, Any]) -> str:
        """تحديد جودة المقطع"""
        try:
            # بناءً على مدة المقطع وعدد المشاهدات
            duration = entry.get('duration', 0)
            views = entry.get('view_count', 0)
            
            # مقاطع قصيرة جداً أو طويلة جداً = جودة منخفضة
            if duration < 30 or duration > 1800:  # أقل من 30 ثانية أو أكثر من 30 دقيقة
                return 'low'
            
            # مقاطع بمشاهدات عالية = جودة عالية
            if views > 1000000:
                return 'high'
            elif views > 100000:
                return 'medium'
            else:
                return 'low'
                
        except Exception:
            return 'medium'
    
    def _extract_artist(self, title: str, uploader: str) -> str:
        """استخراج اسم الفنان"""
        try:
            # أنماط شائعة لاستخراج اسم الفنان
            patterns = [
                r'^([^-]+)\s*-',  # "Artist - Song"
                r'^([^–]+)\s*–',  # "Artist – Song" (em dash)
                r'([^|]+)\s*\|',  # "Artist | Song"
                r'([^•]+)\s*•',   # "Artist • Song"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title.strip())
                if match:
                    artist = match.group(1).strip()
                    if len(artist) > 2 and len(artist) < 50:
                        return artist
            
            # إذا لم نجد نمط، نستخدم اسم القناة
            return uploader
            
        except Exception:
            return uploader
    
    def _clean_search_query(self, query: str) -> str:
        """تنظيف استعلام البحث"""
        try:
            # إزالة الكلمات غير المرغوبة
            unwanted_words = ['official', 'video', 'audio', 'lyrics', 'hd', '4k']
            
            # تنظيف أساسي
            clean_query = query.strip()
            
            # إزالة علامات الترقيم الزائدة
            clean_query = re.sub(r'[^\w\s\u0600-\u06FF-]', ' ', clean_query)
            
            # إزالة المسافات الزائدة
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()
            
            return clean_query
            
        except Exception:
            return query
    
    async def get_stream_url(self, track_id: str) -> Optional[str]:
        """الحصول على رابط التشغيل"""
        try:
            if not self.is_available:
                return None
            
            url = f"https://www.youtube.com/watch?v={track_id}"
            
            # استخراج معلومات الستريم
            loop = asyncio.get_event_loop()
            stream_info = await loop.run_in_executor(
                None,
                self._extract_stream_info,
                url
            )
            
            return stream_info.get('url') if stream_info else None
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على رابط التشغيل: {e}")
            return None
    
    def _extract_stream_info(self, url: str) -> Optional[Dict[str, Any]]:
        """استخراج معلومات الستريم"""
        try:
            with yt_dlp.YoutubeDL({
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'quiet': True,
                'no_warnings': True
            }) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and 'url' in info:
                    return {
                        'url': info['url'],
                        'title': info.get('title', ''),
                        'duration': info.get('duration', 0)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج معلومات الستريم: {e}")
            return None
    
    async def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المقطع"""
        try:
            if not self.is_available:
                return None
            
            url = f"https://www.youtube.com/watch?v={track_id}"
            
            # استخراج معلومات المقطع
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_track_info,
                url
            )
            
            return info
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معلومات المقطع: {e}")
            return None
    
    def _extract_track_info(self, url: str) -> Optional[Dict[str, Any]]:
        """استخراج معلومات المقطع"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    return self._format_youtube_result(info)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج معلومات المقطع: {e}")
            return None
    
    async def download_track(self, track_id: str, output_path: str) -> Optional[str]:
        """تنزيل المقطع الصوتي"""
        try:
            if not self.is_available:
                return None
            
            url = f"https://www.youtube.com/watch?v={track_id}"
            
            # إعدادات التنزيل
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': f"{output_path}/%(title)s.%(ext)s",
                'quiet': True,
                'no_warnings': True
            }
            
            # تنزيل في thread منفصل
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._download_track,
                url,
                ydl_opts
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ فشل في تنزيل المقطع: {e}")
            return None
    
    def _download_track(self, url: str, ydl_opts: Dict[str, Any]) -> Optional[str]:
        """تنزيل المقطع الفعلي"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # استخراج معلومات الملف
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # تنزيل الملف
                    ydl.download([url])
                    
                    # إرجاع مسار الملف
                    filename = ydl.prepare_filename(info)
                    return filename.rsplit('.', 1)[0] + '.mp3'
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في التنزيل الفعلي: {e}")
            return None
    
    def is_youtube_url(self, url: str) -> bool:
        """التحقق من أن الرابط من YouTube"""
        try:
            parsed = urlparse(url)
            return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com']
        except Exception:
            return False
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """استخراج معرف الفيديو من الرابط"""
        try:
            parsed = urlparse(url)
            
            if parsed.netloc == 'youtu.be':
                return parsed.path[1:]
            elif 'youtube.com' in parsed.netloc:
                if 'watch' in parsed.path:
                    return parse_qs(parsed.query).get('v', [None])[0]
                elif 'embed' in parsed.path:
                    return parsed.path.split('/')[-1]
            
            return None
            
        except Exception:
            return None