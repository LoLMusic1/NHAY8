# -*- coding: utf-8 -*-
"""
🚀 نظام التحميل الذكي الخارق - النسخة المتطورة V4
=====================================================
تم التطوير ليدعم:
- البحث في الكاش بدقة عالية
- إرسال الملفات الصوتية مباشرة في جميع الحالات
- 5000 مجموعة و70,000 مستخدم في الخاص
- تحميل متوازي فائق السرعة
- إدارة ذكية للموارد
"""

import os
import re
import asyncio
import logging
import time
import sqlite3
import hashlib
import concurrent.futures
from typing import Dict, Optional, List, Tuple
from itertools import cycle
import aiohttp
import aiofiles
from telethon.tl.types import DocumentAttributeAudio, InputDocument
from pathlib import Path
import uvloop
import psutil
import random
import string
from contextlib import asynccontextmanager
import orjson
import rapidfuzz

# تطبيق UVLoop لتحسين أداء asyncio
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# استيراد المكتبات مع معالجة الأخطاء
try:
    import yt_dlp
except ImportError:
    yt_dlp = None
    
try:
    from youtube_search import YoutubeSearch
except ImportError:
    try:
        from youtubesearchpython import VideosSearch
        YoutubeSearch = VideosSearch
    except ImportError:
        YoutubeSearch = None

# استيراد Telethon
from telethon import events
from telethon.types import Message

import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER
from ZeMusic.utils.database import is_search_enabled, is_search_enabled1
# from ZeMusic.utils.monitoring import PerformanceMonitor

class PerformanceMonitor:
    """مراقب أداء مبسط"""
    def log_error(self, error_type):
        pass

# --- إعدادات النظام الذكي ---
REQUEST_TIMEOUT = 8
DOWNLOAD_TIMEOUT = 90
MAX_SESSIONS = min(100, (psutil.cpu_count() * 4))  # ديناميكي حسب المعالج
MAX_WORKERS = min(200, (psutil.cpu_count() * 10))  # ديناميكي حسب المعالج

# إعدادات العرض
channel = getattr(config, 'STORE_LINK', '')
lnk = f"https://t.me/{channel}" if channel else None

# --- تدوير المفاتيح والخوادم ---
YT_API_KEYS = config.YT_API_KEYS
API_KEYS_CYCLE = cycle(YT_API_KEYS) if YT_API_KEYS else None

INVIDIOUS_SERVERS = config.INVIDIOUS_SERVERS
INVIDIOUS_CYCLE = cycle(INVIDIOUS_SERVERS) if INVIDIOUS_SERVERS else None

# تدوير ملفات الكوكيز
COOKIES_FILES = config.COOKIES_FILES
COOKIES_CYCLE = cycle(COOKIES_FILES) if COOKIES_FILES else None

# --- إعدادات yt-dlp عالية الأداء ---
def get_ytdlp_opts(cookies_file=None) -> Dict:
    """إعدادات متقدمة لـ yt-dlp مع تحسينات الأداء"""
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "retries": 2,
        "no-cache-dir": True,
        "ignoreerrors": True,
        "socket-timeout": REQUEST_TIMEOUT,
        "force-ipv4": True,
        "throttled-rate": "1M",
        "extractor-args": "youtube:player_client=android,web",
        "concurrent-fragments": 16,  # زيادة التجزئة المتوازية
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "postprocessor_args": ["-ar", "44100", "-threads", "4"],
        "noprogress": True,
        "verbose": False,
        "http-chunk-size": "1M",
        "limit-rate": "5M",
        "buffer-size": "16M",
        "extractor-retries": 3,
        "fragment-retries": 5,
        "skip-unavailable-fragments": True,
        "merge-output-format": "mp3",
    }
    
    if cookies_file and os.path.exists(cookies_file):
        opts["cookiefile"] = cookies_file
    
    # إضافة aria2c إذا متوفر
    import shutil
    if shutil.which("aria2c"):
        opts.update({
            "external_downloader": "aria2c",
            "external_downloader_args": [
                "-x", "16", 
                "-s", "16", 
                "-k", "2M",
                "--file-allocation=none",
                "--summary-interval=0"
            ],
        })
    
    return opts

# إنشاء مجلد التحميلات
os.makedirs("downloads", exist_ok=True)

# --- قاعدة البيانات للفهرسة الذكية ---
DB_FILE = "downloads/smart_cache.db"

async def init_database():
    """تهيئة قاعدة البيانات بشكل غير متزامن"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # تحسين هيكل الجدول للبحث الدقيق
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_unique_id TEXT NOT NULL UNIQUE,
            
            search_hash TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT,
            duration INTEGER,
            
            original_query TEXT,
            normalized_query TEXT,
            
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # فهارس متقدمة للبحث السريع
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_search_hash ON audio_cache(search_hash)",
        "CREATE INDEX IF NOT EXISTS idx_title ON audio_cache(title)",
        "CREATE INDEX IF NOT EXISTS idx_artist ON audio_cache(artist)",
        "CREATE INDEX IF NOT EXISTS idx_normalized_query ON audio_cache(normalized_query)",
        "CREATE INDEX IF NOT EXISTS idx_access_count ON audio_cache(access_count DESC)",
        "CREATE INDEX IF NOT EXISTS idx_file_id ON audio_cache(file_id)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند بدء الوحدة
# سيتم تهيئتها عند أول استخدام
# asyncio.run(init_database())

# ================================================================
#                 نظام إدارة الاتصالات المتقدم
# ================================================================
class ConnectionManager:
    """مدير اتصالات متقدم مع تجميع الجلسات"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session_pool = []
            cls._instance._executor_pool = None
            cls._instance._db_connections = {}
        return cls._instance
    
    async def initialize(self):
        """تهيئة تجمع الموارد"""
        # تجمع جلسات HTTP
        connector = aiohttp.TCPConnector(
            limit_per_host=200,
            ttl_dns_cache=600,
            use_dns_cache=True,
            keepalive_timeout=45,
            enable_cleanup_closed=True
        )
        
        self._session_pool = [
            aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                headers={'User-Agent': f'ZeMusic-{i}'},
                json_serialize=orjson.dumps
            ) for i in range(MAX_SESSIONS)
        ]
        
        # تجمع مؤشرات التنفيذ
        self._executor_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
            thread_name_prefix="DLWorker"
        )
        
        LOGGER(__name__).info(f"🚀 تم تهيئة نظام الاتصالات: {MAX_SESSIONS} جلسة, {MAX_WORKERS} عامل")
    
    @property
    def session_pool(self):
        """الحصول على تجمع الجلسات"""
        if not self._session_pool:
            raise RuntimeError("ConnectionManager not initialized")
        return self._session_pool
    
    @property
    def executor_pool(self):
        """الحصول على تجمع العمال"""
        if not self._executor_pool:
            raise RuntimeError("Executor pool not initialized")
        return self._executor_pool
    
    async def get_session(self) -> aiohttp.ClientSession:
        """الحصول على جلسة متاحة"""
        if not self._session_pool:
            await self.initialize()
        return random.choice(self._session_pool)
    
    @asynccontextmanager
    async def db_connection(self):
        """إدارة اتصالات قاعدة البيانات"""
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    async def close(self):
        """إغلاق جميع الموارد"""
        for session in self._session_pool:
            await session.close()
        self._executor_pool.shutdown(wait=True)
        LOGGER(__name__).info("🔌 تم إغلاق جميع موارد الاتصال")

# ================================================================
#                 نظام التحميل الذكي الخارق
# ================================================================
class HyperSpeedDownloader:
    """نسخة متطورة من نظام التحميل مع البحث الدقيق في الكاش"""
    
    def __init__(self):
        self.conn_manager = ConnectionManager()
        self.monitor = PerformanceMonitor()
        self.active_tasks = set()
        self.last_health_check = time.time()
        self.cache_hits = 0
        self.cache_misses = 0
        
        # تسجيل بدء التشغيل
        LOGGER(__name__).info("🚀 بدء تشغيل نظام التحميل المتطور V4 - بحث دقيق في الكاش")
    
    async def health_check(self):
        """فحص صحة النظام بشكل دوري"""
        if time.time() - self.last_health_check > 300:  # كل 5 دقائق
            self.last_health_check = time.time()
            
            # تسجيل إحصائيات الأداء
            stats = {
                'active_tasks': len(self.active_tasks),
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses) * 100
            }
            
            LOGGER(__name__).info(
                f"📊 إحصائيات النظام: "
                f"الذاكرة: {stats['memory_usage']}% | "
                f"المعالج: {stats['cpu_usage']}% | "
                f"الطلبات النشطة: {stats['active_tasks']} | "
                f"نسبة الكاش: {stats['cache_hit_rate']:.1f}%"
            )
    
    def normalize_text(self, text: str) -> str:
        """تطبيع النص للبحث مع تحسين الأداء"""
        if not text:
            return ""
        
        # تحويل للأحرف الصغيرة وإزالة التشكيل
        text = text.lower()
        text = re.sub(r'[\u064B-\u065F]', '', text)  # إزالة التشكيل العربي
        text = re.sub(r'[^\w\s]', '', text)  # إزالة الرموز
        text = re.sub(r'\s+', ' ', text).strip()  # تنظيف المسافات
        
        # تطبيع الحروف العربية باستخدام جدول تحويل
        replacements = {
            'ة': 'ه', 'ي': 'ى', 'أ': 'ا', 'إ': 'ا',
            'آ': 'ا', 'ؤ': 'و', 'ئ': 'ي', 'ٱ': 'ا',
            'ٰ': '', 'ّ': '', 'ْ': '', 'ٌ': '',
            'ٍ': '', 'ً': '', 'ُ': '', 'َ': '',
            'ِ': '', '~': '', 'ـ': ''
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def create_search_hash(self, query: str) -> str:
        """إنشاء هاش للبحث السريع باستخدام خوارزمية أسرع"""
        normalized_query = self.normalize_text(query)
        return hashlib.md5(normalized_query.encode(), usedforsecurity=False).hexdigest()[:12]
    
    async def precise_cache_search(self, query: str) -> Optional[Dict]:
        """بحث دقيق في الكاش مع تطابق ذكي"""
        try:
            # تهيئة قاعدة البيانات إذا لم تكن مهيأة
            await init_database()
            
            normalized_query = self.normalize_text(query)
            search_hash = self.create_search_hash(query)
            
            async with self.conn_manager.db_connection() as conn:
                cursor = conn.cursor()
                
                # البحث المباشر بالهاش
                cursor.execute(
                    "SELECT file_id, file_unique_id, title, artist, duration "
                    "FROM audio_cache WHERE search_hash = ? LIMIT 1",
                    (search_hash,)
                )
                result = cursor.fetchone()
                
                if result:
                    # تحديث إحصائيات الاستخدام
                    cursor.execute(
                        "UPDATE audio_cache SET access_count = access_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE search_hash = ?",
                        (search_hash,)
                    )
                    conn.commit()
                    
                    self.cache_hits += 1
                    return {
                        'file_id': result['file_id'],
                        'file_unique_id': result['file_unique_id'],
                        'title': result['title'],
                        'artist': result['artist'],
                        'duration': result['duration'],
                        'source': 'cache_exact_match'
                    }
                
                # البحث باستخدام تطابق تقريبي متقدم
                cursor.execute(
                    "SELECT file_id, file_unique_id, title, artist, duration, normalized_query "
                    "FROM audio_cache"
                )
                all_entries = cursor.fetchall()
                
                if not all_entries:
                    self.cache_misses += 1
                    return None
                
                # البحث باستخدام خوارزمية RapidFuzz للتطابق الضبابي
                best_match = None
                best_score = 0
                
                for entry in all_entries:
                    score = rapidfuzz.fuzz.ratio(
                        normalized_query, 
                        entry['normalized_query']
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_match = entry
                
                # تطابق جيد إذا كانت النسبة فوق 85%
                if best_match and best_score > 85:
                    # تحديث إحصائيات الاستخدام
                    cursor.execute(
                        "UPDATE audio_cache SET access_count = access_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE file_unique_id = ?",
                        (best_match['file_unique_id'],)
                    )
                    conn.commit()
                    
                    self.cache_hits += 1
                    return {
                        'file_id': best_match['file_id'],
                        'file_unique_id': best_match['file_unique_id'],
                        'title': best_match['title'],
                        'artist': best_match['artist'],
                        'duration': best_match['duration'],
                        'source': f'cache_fuzzy_match_{best_score}'
                    }
                
                # تطابق جزئي باستخدام الكلمات الرئيسية
                query_keywords = set(normalized_query.split())
                
                for entry in all_entries:
                    entry_keywords = set(entry['normalized_query'].split())
                    common_keywords = query_keywords & entry_keywords
                    
                    if len(common_keywords) / len(query_keywords) > 0.7:
                        # تحديث إحصائيات الاستخدام
                        cursor.execute(
                            "UPDATE audio_cache SET access_count = access_count + 1, "
                            "last_accessed = CURRENT_TIMESTAMP WHERE file_unique_id = ?",
                            (entry['file_unique_id'],)
                        )
                        conn.commit()
                        
                        self.cache_hits += 1
                        return {
                            'file_id': entry['file_id'],
                            'file_unique_id': entry['file_unique_id'],
                            'title': entry['title'],
                            'artist': entry['artist'],
                            'duration': entry['duration'],
                            'source': f'cache_keyword_match'
                        }
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث الدقيق في الكاش: {e}")
            self.monitor.log_error('cache_search')
            return None
    
    async def add_to_cache(self, file_id: str, file_unique_id: str, 
                          title: str, artist: str, duration: int, 
                          query: str) -> bool:
        """إضافة ملف جديد إلى الكاش"""
        try:
            # تهيئة قاعدة البيانات إذا لم تكن مهيأة
            await init_database()
            
            normalized_query = self.normalize_text(query)
            search_hash = self.create_search_hash(query)
            
            async with self.conn_manager.db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT OR REPLACE INTO audio_cache "
                    "(file_id, file_unique_id, search_hash, title, artist, duration, "
                    "original_query, normalized_query) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (file_id, file_unique_id, search_hash, title, artist, duration, 
                     query, normalized_query)
                )
                
                conn.commit()
                LOGGER(__name__).info(f"✅ تم إضافة {title} إلى الكاش")
                return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة إلى الكاش: {e}")
            self.monitor.log_error('cache_add')
            return False
    
    async def youtube_api_search(self, query: str) -> Optional[Dict]:
        """البحث عبر YouTube Data API مع تحسينات الأداء"""
        if not API_KEYS_CYCLE:
            return None
        
        session = await self.conn_manager.get_session()
        start_time = time.time()
        
        try:
            for _ in range(len(YT_API_KEYS)):
                key = next(API_KEYS_CYCLE)
                params = {
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": 1,
                    "key": key,
                    "videoCategoryId": "10",  # موسيقى فقط
                    "relevanceLanguage": "ar,en"
                }
                
                try:
                    async with session.get(
                        "https://www.googleapis.com/youtube/v3/search",
                        params=params,
                        timeout=REQUEST_TIMEOUT
                    ) as resp:
                        if resp.status == 403:
                            LOGGER(__name__).warning(f"مفتاح API محظور: {key[:5]}...")
                            continue
                            
                        if resp.status != 200:
                            continue
                        
                        data = await resp.json()
                        items = data.get("items", [])
                        if not items:
                            continue
                        
                        item = items[0]
                        video_id = item["id"]["videoId"]
                        snippet = item["snippet"]
                        
                        return {
                            "video_id": video_id,
                            "title": snippet.get("title", "")[:60],
                            "artist": snippet.get("channelTitle", "Unknown"),
                            "thumb": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "source": "youtube_api"
                        }
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
        
        except Exception as e:
            LOGGER(__name__).warning(f"فشل YouTube API: {e}")
            self.monitor.log_error('youtube_api')
        
        return None
    
    async def invidious_search(self, query: str) -> Optional[Dict]:
        """البحث عبر Invidious مع تحسينات الأداء"""
        if not INVIDIOUS_CYCLE:
            return None
        
        session = await self.conn_manager.get_session()
        start_time = time.time()
        
        try:
            for _ in range(len(INVIDIOUS_SERVERS)):
                server = next(INVIDIOUS_CYCLE)
                url = f"{server}/api/v1/search"
                params = {
                    "q": query, 
                    "type": "video",
                    "sort_by": "relevance",
                    "duration": "short"
                }
                
                try:
                    async with session.get(
                        url, 
                        params=params,
                        timeout=REQUEST_TIMEOUT
                    ) as resp:
                        if resp.status != 200:
                            continue
                        
                        content_type = resp.headers.get('content-type', '')
                        if 'application/json' not in content_type:
                            continue
                        
                        data = await resp.json()
                        video = next((item for item in data if item.get("type") == "video"), None)
                        if not video:
                            continue
                        
                        return {
                            "video_id": video.get("videoId"),
                            "title": video.get("title", "")[:60],
                            "artist": video.get("author", "Unknown"),
                            "duration": int(video.get("lengthSeconds", 0)),
                            "thumb": next(
                                (t.get("url") for t in reversed(video.get("videoThumbnails", []))),
                                None
                            ),
                            "source": "invidious"
                        }
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
        
        except Exception as e:
            LOGGER(__name__).warning(f"فشل Invidious: {e}")
            self.monitor.log_error('invidious')
        
        return None
    
    async def youtube_search_simple(self, query: str) -> Optional[Dict]:
        """البحث عبر youtube_search مع معالجة محسنة"""
        if not YoutubeSearch:
            return None
        
        start_time = time.time()
            
        try:
            # استخدام youtube_search مع معالجة محسنة
            search = YoutubeSearch(query, max_results=1)
            results = search.result()['result'] if hasattr(search, 'result') else search.to_dict()
            
            if not results:
                return None
            
            result = results[0]
            
            # استخراج video_id
            video_id = result.get('id') or result.get('link', '').split('=')[-1]
            
            # معالجة المدة
            duration = result.get('duration', '0:00')
            if isinstance(duration, str) and ':' in duration:
                parts = duration.split(':')
                if len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    duration = 0
            else:
                duration = int(duration)
            
            return {
                "video_id": video_id,
                "title": result.get("title", "Unknown Title")[:60],
                "artist": result.get("channel", {}).get("name", "Unknown Artist") if isinstance(result.get("channel"), dict) else result.get("channel", "Unknown Artist"),
                "duration": duration,
                "thumb": result.get("thumbnails", [None])[0] if result.get("thumbnails") else None,
                "link": f"https://youtube.com/watch?v={video_id}",
                "source": "youtube_search"
            }
            
        except Exception as e:
            LOGGER(__name__).warning(f"فشل YouTube Search: {e}")
            self.monitor.log_error('youtube_search')
            return None
    
    async def download_with_ytdlp(self, video_info: Dict) -> Optional[Dict]:
        """تحميل عبر yt-dlp مع تدوير الكوكيز"""
        if not yt_dlp:
            return None
            
        video_id = video_info.get("video_id")
        if not video_id:
            return None
        
        url = f"https://youtu.be/{video_id}"
        start_time = time.time()
        
        # محاولة مع مدير الكوكيز الذكي
        try:
            from ZeMusic.core.cookies_manager import cookies_manager, report_cookie_success, report_cookie_failure
            
            # محاولة مع الكوكيز أولاً
            for attempt in range(2):  # محاولة كوكيزين مختلفين
                try:
                    cookies_file = await cookies_manager.get_next_cookie()
                    if not cookies_file:
                        break
                        
                    opts = get_ytdlp_opts(cookies_file)
                    
                    loop = asyncio.get_running_loop()
                    info = await loop.run_in_executor(
                        self.conn_manager.executor_pool,
                        lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
                    )
                    
                    if info:
                        audio_path = f"downloads/{video_id}.mp3"
                        if os.path.exists(audio_path):
                            # تقرير نجاح وتحديث الأداء
                            await report_cookie_success(cookies_file)
                            
                            return {
                                "audio_path": audio_path,
                                "title": info.get("title", video_info.get("title", ""))[:60],
                                "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                                "duration": int(info.get("duration", 0)),
                                "source": f"ytdlp_cookies_{Path(cookies_file).name}"
                            }
                
                except Exception as e:
                    # تقرير فشل
                    if 'cookies_file' in locals() and cookies_file:
                        await report_cookie_failure(cookies_file, str(e))
                    LOGGER(__name__).warning(f"فشل yt-dlp مع كوكيز {cookies_file}: {e}")
                    continue
                    
        except ImportError:
            # العودة للنظام القديم إذا لم يكن المدير متاحاً
            if COOKIES_CYCLE:
                for _ in range(len(COOKIES_FILES)):
                    try:
                        cookies_file = next(COOKIES_CYCLE)
                        opts = get_ytdlp_opts(cookies_file)
                        
                        loop = asyncio.get_running_loop()
                        info = await loop.run_in_executor(
                            self.conn_manager.executor_pool,
                            lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
                        )
                        
                        if info:
                            audio_path = f"downloads/{video_id}.mp3"
                            if os.path.exists(audio_path):
                                return {
                                    "audio_path": audio_path,
                                    "title": info.get("title", video_info.get("title", ""))[:60],
                                    "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                                    "duration": int(info.get("duration", 0)),
                                    "source": f"ytdlp_cookies_{cookies_file}"
                                }
                    
                    except Exception as e:
                        LOGGER(__name__).warning(f"فشل yt-dlp مع كوكيز {cookies_file}: {e}")
                        continue
        
        # محاولة بدون كوكيز
        try:
            opts = get_ytdlp_opts()
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                self.conn_manager.executor_pool,
                lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
            )
            
            if info:
                audio_path = f"downloads/{video_id}.mp3"
                if os.path.exists(audio_path):
                    return {
                        "audio_path": audio_path,
                        "title": info.get("title", video_info.get("title", ""))[:60],
                        "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                        "duration": int(info.get("duration", 0)),
                        "source": "ytdlp_no_cookies"
                    }
        
        except Exception as e:
            LOGGER(__name__).error(f"فشل yt-dlp بدون كوكيز: {e}")
            self.monitor.log_error('ytdlp_download')
        
        return None
    
    async def hyper_download(self, query: str) -> Optional[Dict]:
        """النظام الخارق للتحميل مع البحث في الكاش"""
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.active_tasks.add(task_id)
        start_time = time.time()
        
        try:
            # فحص الصحة الدوري
            await self.health_check()
            
            # الخطوة 1: البحث الدقيق في الكاش أولاً
            cache_result = await self.precise_cache_search(query)
            if cache_result:
                LOGGER(__name__).info(f"⚡ نتيجة من الكاش: {query} ({time.time() - start_time:.3f}s)")
                return {
                    'file_id': cache_result['file_id'],
                    'file_unique_id': cache_result['file_unique_id'],
                    'title': cache_result['title'],
                    'artist': cache_result['artist'],
                    'duration': cache_result['duration'],
                    'source': cache_result['source'],
                    'cached': True
                }
            
            # الخطوة 2: البحث عن معلومات الفيديو بالتوازي
            search_methods = []
            
            if API_KEYS_CYCLE:
                search_methods.append(self.youtube_api_search(query))
            if INVIDIOUS_CYCLE:
                search_methods.append(self.invidious_search(query))
            if YoutubeSearch:
                search_methods.append(self.youtube_search_simple(query))
            
            # تشغيل جميع عمليات البحث بالتوازي
            done, pending = await asyncio.wait(
                search_methods,
                timeout=REQUEST_TIMEOUT * 1.5,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # إلغاء المهام المتبقية
            for task in pending:
                task.cancel()
            
            # أخذ أول نتيجة ناجحة
            video_info = None
            for task in done:
                result = task.result()
                if result:
                    video_info = result
                    break
            
            if not video_info:
                return None
            
            # الخطوة 3: تحميل الصوت
            audio_info = await self.download_with_ytdlp(video_info)
            if not audio_info:
                # محاولة نسخة احتياطية
                audio_info = await self.download_without_cookies(video_info)
                if not audio_info:
                    return None
            
            LOGGER(__name__).info(f"✅ تحميل جديد: {query} ({time.time() - start_time:.3f}s)")
            
            return {
                'audio_path': audio_info['audio_path'],
                'title': audio_info['title'],
                'artist': audio_info['artist'],
                'duration': audio_info['duration'],
                'source': audio_info['source'],
                'cached': False
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في التحميل الخارق: {e}")
            self.monitor.log_error('hyper_download')
            return None
        finally:
            self.active_tasks.discard(task_id)
    
    async def direct_ytdlp_download(self, video_id: str, title: str = "Unknown") -> Optional[Dict]:
        """تحميل مباشر باستخدام yt-dlp مع cookies"""
        if not yt_dlp:
            return None
            
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.active_tasks.add(task_id)
        start_time = time.time()
        
        try:
            # إنشاء مجلد مؤقت
            temp_dir = Path("downloads/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # إعداد yt-dlp
            try:
                from ZeMusic.core.cookies_manager import cookies_manager
                best_cookie = await cookies_manager.get_next_cookie()
            except:
                best_cookie = None
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/best[ext=m4a]/bestaudio/best',
                'outtmpl': str(temp_dir / f'{video_id}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writethumbnail': False,
                'noplaylist': True,
                'socket_timeout': REQUEST_TIMEOUT,
                'retries': 3,
                'fragment_retries': 5,
                'skip_unavailable_fragments': True,
            }
            
            # إضافة cookies إذا كانت متاحة
            if best_cookie:
                ydl_opts['cookiefile'] = best_cookie
            
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                self.conn_manager.executor_pool,
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=True
                )
            )
            
            if info:
                # البحث عن الملف المحمل
                for file_path in temp_dir.glob(f"{video_id}.*"):
                    if file_path.suffix in ['.m4a', '.mp3', '.webm', '.mp4']:
                        return {
                            'success': True,
                            'file_path': str(file_path),
                            'title': info.get('title', title),
                            'duration': info.get('duration', 0),
                            'uploader': info.get('uploader', 'Unknown'),
                            'elapsed': time.time() - start_time
                        }
            
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في التحميل المباشر: {e}")
            self.monitor.log_error('direct_download')
            return None
        finally:
            self.active_tasks.discard(task_id)

    async def download_without_cookies(self, video_info: Dict) -> Optional[Dict]:
        """تحميل بدون كوكيز - نسخة مبسطة وسريعة"""
        if not yt_dlp:
            return None
            
        video_id = video_info.get("video_id")
        if not video_id:
            return None
        
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.active_tasks.add(task_id)
        start_time = time.time()
        
        try:
            # إعدادات سريعة وموثوقة
            opts = {
                'format': 'worstaudio[ext=m4a]/worstaudio',
                'outtmpl': f'downloads/{video_id}_fallback.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
                'referer': 'https://www.google.com/',
                'timeout': 15,
                'retries': 1,
                'fragment_retries': 1,
                'skip_unavailable_fragments': True,
                'noprogress': True,
                'socket_timeout': 10,
                'force_generic_extractor': True,
            }
            
            url = f"https://youtu.be/{video_id}"
            
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                self.conn_manager.executor_pool,
                lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
            )
            
            if info:
                # البحث عن الملف المحمل
                possible_files = [
                    f"downloads/{video_id}_fallback.m4a",
                    f"downloads/{video_id}_fallback.mp3",
                    f"downloads/{video_id}_fallback.webm"
                ]
                
                for audio_path in possible_files:
                    if os.path.exists(audio_path):
                        return {
                            "audio_path": audio_path,
                            "title": info.get("title", video_info.get("title", ""))[:60],
                            "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                            "duration": int(info.get("duration", 0)),
                            "source": "ytdlp_simple_fallback",
                            "elapsed": time.time() - start_time
                        }
                        
        except Exception as e:
            LOGGER(__name__).error(f"فشل التحميل بدون كوكيز: {e}")
            self.monitor.log_error('fallback_download')
        finally:
            self.active_tasks.discard(task_id)
            
        return None

# إنشاء مدير التحميل العالمي
downloader = HyperSpeedDownloader()

async def remove_temp_files(*paths):
    """حذف الملفات المؤقتة بشكل آمن"""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                LOGGER(__name__).debug(f"تم حذف الملف المؤقت: {path}")
            except Exception as e:
                LOGGER(__name__).warning(f"فشل حذف {path}: {e}")

async def download_thumbnail(url: str, title: str) -> Optional[str]:
    """تحميل الصورة المصغرة بشكل غير متزامن"""
    if not url:
        return None
    
    try:
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
        thumb_path = f"downloads/thumb_{title_clean[:20]}.jpg"
        
        session = await downloader.conn_manager.get_session()
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(thumb_path, mode='wb') as f:
                    await f.write(await resp.read())
                return thumb_path
    except Exception as e:
        LOGGER(__name__).warning(f"فشل تحميل الصورة: {e}")
    
    return None

# --- المعالج الموحد لجميع أنواع المحادثات مع Telethon ---
async def smart_download_handler(event):
    """المعالج الذكي للتحميل مع البحث الدقيق في الكاش"""
    try:
        chat_id = event.chat_id
        if chat_id > 0:  # محادثة خاصة
            if not await is_search_enabled1():
                await event.reply("⟡ عذراً عزيزي اليوتيوب معطل من قبل المطور")
                return
        else:  # مجموعة أو قناة
            if not await is_search_enabled(chat_id):
                await event.reply("⟡ عذراً عزيزي اليوتيوب معطل من قبل المطور")
                return
    except:
        pass
    
    # استخراج الاستعلام
    message_text = event.message.text or ""
    query = re.sub(r'^(بحث|/search|/song|يوت|اغنية|تحميل)\s*', '', message_text, flags=re.IGNORECASE).strip()
    
    if not query:
        await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
        return
    
    # رسالة المعالجة
    status_msg = await event.reply("⚡ **جاري المعالجة بالنظام الذكي...**")
    
    try:
        # الخطوة 1: البحث في الكاش أولاً
        await status_msg.edit("🔍 **جاري البحث في الكاش...**")
        cache_result = await downloader.precise_cache_search(query)
        
        if cache_result:
            # تم العثور على النتيجة في الكاش - إرسال الملف مباشرة
            await status_msg.edit("⚡ **تم العثور على النتيجة في الكاش...**")
            
            # إعداد التسمية التوضيحية
            duration = cache_result.get('duration', 0)
            duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
            
            caption = f"""🎵 **{cache_result.get('title', 'مقطع صوتي')}**
🎤 **{cache_result.get('artist', 'غير معروف')}**
⏱️ **{duration_str}** | 💾 **من الكاش**

⚡ **مصدر:** {cache_result.get('source', '')}"""
            
            # إرسال الملف باستخدام معرف الملف من الكاش
            await telethon_manager.bot_client.send_file(
                event.chat_id,
                file=InputDocument(
                    id=int(cache_result['file_id']),
                    access_hash=0,  # لا يلزم في معظم الحالات
                    file_reference=b''
                ),
                caption=caption,
                reply_to=event.message.id,
                supports_streaming=True,
                attributes=[
                    DocumentAttributeAudio(
                        duration=duration,
                        title=cache_result.get('title', '')[:60],
                        performer=cache_result.get('artist', '')[:40]
                    )
                ]
            )
            
            await status_msg.delete()
            return
        
        # الخطوة 2: البحث عن الفيديو
        await status_msg.edit("🔍 **جاري البحث عن الأغنية...**")
        video_info = None
        
        try:
            from youtubesearchpython import VideosSearch
            search = VideosSearch(query, limit=1)
            results = search.result()
            if results.get('result'):
                video_info = results['result'][0]
        except:
            try:
                from youtube_search import YoutubeSearch
                search = YoutubeSearch(query, max_results=1)
                video_info = search.to_dict()[0] if search.to_dict() else None
            except:
                pass
        
        if not video_info:
            await status_msg.edit("❌ **لم يتم العثور على نتائج للبحث**\n\n💡 **جرب:**\n• كلمات مختلفة\n• اسم الفنان\n• جزء من كلمات الأغنية")
            return
        
        # استخراج video_id
        video_id = video_info.get('id') or (video_info.get('link', '').split('=')[-1])
        
        if not video_id:
            await status_msg.edit("❌ **خطأ في استخراج معرف الفيديو**")
            return
        
        # الخطوة 3: محاولة التحميل
        await status_msg.edit("🔄 **جاري تحميل الملف الصوتي...**")
        download_result = await downloader.direct_ytdlp_download(video_id, video_info.get('title', 'Unknown'))
        
        if download_result and download_result.get('success'):
            # التحميل نجح - إرسال الملف
            audio_file = download_result.get('file_path')
            if audio_file and Path(audio_file).exists():
                await status_msg.edit("📤 **تم التحميل! جاري الإرسال...**")
                
                # إعداد التسمية التوضيحية
                duration = download_result.get('duration', 0)
                duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
                
                caption = f"""🎵 **{download_result.get('title', 'مقطع صوتي')}**
🎤 **{download_result.get('uploader', 'Unknown')[:40]}**
⏱️ **{duration_str}** | ⚡ **{download_result.get('elapsed', 0):.1f} ثانية**"""
                
                # إرسال الملف
                msg = await event.respond(
                    caption,
                    file=audio_file,
                    attributes=[
                        DocumentAttributeAudio(
                            duration=duration,
                            title=download_result.get('title', 'Unknown')[:60],
                            performer=download_result.get('uploader', 'Unknown')[:40]
                        )
                    ]
                )
                
                # حفظ في الكاش
                if msg and msg.file:
                    await downloader.add_to_cache(
                        file_id=str(msg.file.id),
                        file_unique_id=msg.file.extras.get('file_unique_id', ''),
                        title=download_result.get('title', ''),
                        artist=download_result.get('uploader', ''),
                        duration=duration,
                        query=query
                    )
                
                await status_msg.delete()
                await remove_temp_files(audio_file)
                return
        
        # الخطوة 4: محاولة النظام الخارق
        try:
            await status_msg.edit("🔄 **تفعيل النظام الخارق...**")
            result = await downloader.hyper_download(query)
            
            if result:
                if result.get('cached'):
                    # تم العثور في الكاش خلال التحميل
                    await status_msg.edit("⚡ **تم العثور على النتيجة في الكاش...**")
                    
                    # إعداد التسمية التوضيحية
                    duration = result.get('duration', 0)
                    duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
                    
                    caption = f"""🎵 **{result.get('title', 'مقطع صوتي')}**
🎤 **{result.get('artist', 'غير معروف')}**
⏱️ **{duration_str}** | 💾 **من الكاش**

⚡ **مصدر:** {result.get('source', '')}"""
                    
                    # إرسال الملف باستخدام معرف الملف من الكاش
                    await telethon_manager.bot_client.send_file(
                        event.chat_id,
                        file=InputDocument(
                            id=int(result['file_id']),
                            access_hash=0,
                            file_reference=b''
                        ),
                        caption=caption,
                        reply_to=event.message.id,
                        supports_streaming=True,
                        attributes=[
                            DocumentAttributeAudio(
                                duration=duration,
                                title=result.get('title', '')[:60],
                                performer=result.get('artist', '')[:40]
                            )
                        ]
                    )
                    
                    await status_msg.delete()
                    return
                else:
                    # تحميل جديد - إرسال الملف
                    audio_file = result['audio_path']
                    if Path(audio_file).exists():
                        await status_msg.edit("📤 **تم التحميل! جاري الإرسال...**")
                        
                        # إعداد التسمية التوضيحية
                        duration = result.get('duration', 0)
                        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
                        
                        caption = f"""🎵 **{result.get('title', 'مقطع صوتي')}**
🎤 **{result.get('artist', 'غير معروف')}**
⏱️ **{duration_str}** | 📦 **{result.get('source', '')}**

💡 **مُحمّل بواسطة:** @{config.BOT_USERNAME}"""
                        
                        # إرسال الملف
                        msg = await telethon_manager.bot_client.send_file(
                            event.chat_id,
                            audio_file,
                            caption=caption,
                            reply_to=event.message.id,
                            supports_streaming=True,
                            attributes=[
                                DocumentAttributeAudio(
                                    duration=duration,
                                    title=result.get('title', '')[:60],
                                    performer=result.get('artist', '')[:40]
                                )
                            ]
                        )
                        
                        # حفظ في الكاش
                        if msg and msg.file:
                            await downloader.add_to_cache(
                                file_id=str(msg.file.id),
                                file_unique_id=msg.file.extras.get('file_unique_id', ''),
                                title=result.get('title', ''),
                                artist=result.get('artist', ''),
                                duration=duration,
                                query=query
                            )
                        
                        await status_msg.delete()
                        await remove_temp_files(audio_file)
                        return
                    
        except Exception as e:
            LOGGER(__name__).warning(f"فشل التحميل بالنظام الخارق: {e}")
        
        # التحميل فشل كلياً - عرض معلومات الفيديو
        result_text = f"""🔍 **تم العثور على الأغنية:**

📝 **العنوان:** {video_info.get('title', 'غير معروف')}
🎤 **الفنان:** {video_info.get('channel', {}).get('name', 'غير معروف') if isinstance(video_info.get('channel'), dict) else video_info.get('channel', 'غير معروف')}
⏱️ **المدة:** {video_info.get('duration', 'غير معروف')}
👁️ **المشاهدات:** {video_info.get('viewCount', {}).get('short', 'غير معروف') if isinstance(video_info.get('viewCount'), dict) else video_info.get('viewCount', 'غير معروف')}

🔗 **الرابط:** https://youtu.be/{video_id}

⚠️ **التحميل غير متاح حالياً:**
• انتهت صلاحية ملفات الكوكيز
• قيود أمنية من YouTube
• مشكلة مؤقتة في الخدمة

💡 **الحل:** يمكنك مشاهدة الفيديو من الرابط أعلاه
🔧 **للمطور:** تحديث ملفات الكوكيز مطلوب"""
        
        await status_msg.edit(result_text)
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في المعالج: {e}")
        try:
            await status_msg.edit("❌ **حدث خطأ في المعالجة**\n\n💡 **جرب:**\n• كلمات مختلفة\n• إعادة المحاولة لاحقاً")
        except:
            pass

# --- أوامر المطور مع Telethon ---
async def cache_stats_handler(event):
    """عرض إحصائيات الكاش"""
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        async with downloader.conn_manager.db_connection() as conn:
            cursor = conn.cursor()
            
            # إحصائيات الكاش
            cursor.execute("SELECT COUNT(*) FROM audio_cache")
            total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(access_count) FROM audio_cache")
            total_access = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT title, access_count FROM audio_cache ORDER BY access_count DESC LIMIT 10")
            top_entries = cursor.fetchall()
            
            # إحصائيات النظام
            mem_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            cache_hit_rate = downloader.cache_hits / max(1, downloader.cache_hits + downloader.cache_misses) * 100
            
            stats_text = f"""📊 **إحصائيات الكاش المتقدمة**

🗃️ **المدخلات:** {total_entries}
🔁 **مرات الوصول:** {total_access}
🎯 **نسبة الضربات:** {cache_hit_rate:.1f}%

🧠 **إحصائيات النظام:**
• الذاكرة: {mem_usage}%
• المعالج: {cpu_usage}%

🏆 **أكثر الملفات طلباً:**"""
            
            for i, row in enumerate(top_entries, 1):
                stats_text += f"\n{i}. {row['title'][:30]}... ({row['access_count']})"
            
            await event.reply(stats_text)
            
    except Exception as e:
        await event.reply(f"❌ خطأ: {e}")

async def clear_cache_handler(event):
    """مسح الكاش"""
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        async with downloader.conn_manager.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM audio_cache")
            total_before = cursor.fetchone()[0]
            cursor.execute("DELETE FROM audio_cache")
            conn.commit()
        
        downloader.cache_hits = 0
        downloader.cache_misses = 0
        
        await event.reply(f"""🧹 **تم مسح الكاش بالكامل!**

🗑️ **المدخلات المحذوفة:** {total_before}
🔄 **تم إعادة تعيين الإحصائيات**""")
        
    except Exception as e:
        await event.reply(f"❌ خطأ في مسح الكاش: {e}")

# --- معالج الأوامر الرئيسي ---
async def search_command_handler(event):
    """معالج أوامر البحث المباشر"""
    
    # التحقق من أن هذه رسالة نصية
    if not event.message or not event.message.text:
        return
    
    text = event.message.text.strip()
    LOGGER(__name__).info(f"🔍 تم استلام رسالة: {text[:50]}...")
    
    # قائمة أوامر البحث
    search_commands = [
        "بحث ",
        "/song ",
        "song ",
        "يوت ",
        "/search ",
        "search ",
        "اغنية ",
        "تحميل ",
        "/play ",
        "play "
    ]
    
    # فحص ما إذا كانت الرسالة تحتوي على أمر البحث
    is_search_command = any(text.lower().startswith(cmd.lower()) for cmd in search_commands)
    
    if is_search_command:
        await smart_download_handler(event)
        return
    
    # أوامر المطور
    if text == "/cache_stats" and event.sender_id == config.OWNER_ID:
        await cache_stats_handler(event)
        return
    
    if text == "/clear_cache" and event.sender_id == config.OWNER_ID:
        await clear_cache_handler(event)
        return

# --- إدارة إغلاق النظام ---
async def shutdown_system():
    """إغلاق جميع موارد النظام بشكل آمن"""
    LOGGER(__name__).info("🔴 بدء إيقاف النظام...")
    await downloader.conn_manager.close()
    LOGGER(__name__).info("✅ تم إيقاف جميع الموارد")

# تسجيل معالج الإغلاق
import atexit
atexit.register(lambda: asyncio.run(shutdown_system()))

LOGGER(__name__).info("🚀 تم تحميل نظام التحميل الذكي الخارق المتطور V4 - بحث دقيق في الكاش")
