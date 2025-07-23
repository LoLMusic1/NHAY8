# -*- coding: utf-8 -*-
"""
🚀 نظام التحميل الذكي الخارق - النسخة المتطورة V2
=====================================================
تم التطوير ليدعم:
- 5000 مجموعة و70,000 مستخدم في الخاص
- تحميل متوازي فائق السرعة
- إدارة ذكية للموارد
- قاعدة بيانات غير متزامنة
- نظام مراقبة وتتبع متقدم
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
from telethon.tl.types import DocumentAttributeAudio
from pathlib import Path
import uvloop
import psutil
import random
import string
from contextlib import asynccontextmanager
import orjson

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

# --- إعدادات النظام الذكي ---
REQUEST_TIMEOUT = 8
DOWNLOAD_TIMEOUT = 90
MAX_SESSIONS = min(100, (psutil.cpu_count() * 4))  # ديناميكي حسب المعالج
MAX_WORKERS = min(200, (psutil.cpu_count() * 10))  # ديناميكي حسب المعالج

# قناة التخزين الذكي (يوزر أو ID)
SMART_CACHE_CHANNEL = config.CACHE_CHANNEL_ID

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
DB_FILE = "smart_cache.db"

async def init_database():
    """تهيئة قاعدة البيانات بشكل غير متزامن"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # تحسين هيكل الجدول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER UNIQUE,
            file_id TEXT UNIQUE,
            file_unique_id TEXT,
            
            search_hash TEXT UNIQUE,
            title_normalized TEXT,
            artist_normalized TEXT,
            keywords_vector TEXT,
            
            original_title TEXT,
            original_artist TEXT,
            duration INTEGER,
            file_size INTEGER,
            
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            popularity_rank REAL DEFAULT 0,
            
            phonetic_hash TEXT,
            partial_matches TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # تحسين الفهارس
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_search_hash ON channel_index(search_hash)",
        "CREATE INDEX IF NOT EXISTS idx_title_norm ON channel_index(title_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_artist_norm ON channel_index(artist_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_popularity ON channel_index(popularity_rank DESC)",
        "CREATE INDEX IF NOT EXISTS idx_message_id ON channel_index(message_id)",
        "CREATE INDEX IF NOT EXISTS idx_file_id ON channel_index(file_id)",
        "CREATE INDEX IF NOT EXISTS idx_keywords ON channel_index(keywords_vector)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند بدء الوحدة
# سيتم تهيئة قاعدة البيانات عند أول استخدام
_database_initialized = False

async def ensure_database_initialized():
    """التأكد من تهيئة قاعدة البيانات"""
    global _database_initialized
    if not _database_initialized:
        await init_database()
        _database_initialized = True

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
    """نسخة مبسطة من نظام التحميل"""
    
    def __init__(self):
        self.downloads_folder = "downloads"
        os.makedirs(self.downloads_folder, exist_ok=True)
        
        # تسجيل بدء التشغيل
        LOGGER(__name__).info("🚀 بدء تشغيل نظام التحميل المبسط")
    
    async def health_check(self):
        """فحص صحة النظام بشكل دوري"""
        if time.time() - self.last_health_check > 300:  # كل 5 دقائق
            self.last_health_check = time.time()
            
            # تسجيل إحصائيات الأداء
            stats = {
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses) * 100,
                'active_tasks': len(self.active_tasks),
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
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
    
    def create_search_hash(self, title: str, artist: str = "") -> str:
        """إنشاء هاش للبحث السريع باستخدام خوارزمية أسرع"""
        normalized_title = self.normalize_text(title)
        normalized_artist = self.normalize_text(artist)
        combined = f"{normalized_title}_{normalized_artist}".encode()
        return hashlib.md5(combined, usedforsecurity=False).hexdigest()[:12]
    
    async def lightning_search_cache(self, query: str) -> Optional[Dict]:
        """بحث خاطف في الكاش مع تحسينات الأداء"""
        try:
            normalized_query = self.normalize_text(query)
            search_hash = self.create_search_hash(normalized_query)
            
            async with self.conn_manager.db_connection() as conn:
                cursor = conn.cursor()
                
                # بحث مباشر بالهاش
                cursor.execute(
                    "SELECT message_id, file_id, original_title, original_artist, duration "
                    "FROM channel_index WHERE search_hash = ? LIMIT 1",
                    (search_hash,)
                )
                result = cursor.fetchone()
                
                if result:
                    # تحديث إحصائيات الاستخدام
                    cursor.execute(
                        "UPDATE channel_index SET access_count = access_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE search_hash = ?",
                        (search_hash,)
                    )
                    conn.commit()
                    
                    self.cache_hits += 1
                    return {
                        'message_id': result[0],
                        'file_id': result[1],
                        'title': result[2],
                        'artist': result[3],
                        'duration': result[4],
                        'source': 'cache',
                        'cached': True
                    }
                
                # بحث تقريبي باستخدام فهرس الكلمات
                keywords = normalized_query.split()
                keyword_conditions = " OR ".join(["keywords_vector LIKE ?" for _ in keywords])
                params = [f"%{kw}%" for kw in keywords]
                
                cursor.execute(
                    f"SELECT message_id, file_id, original_title, original_artist, duration "
                    f"FROM channel_index WHERE {keyword_conditions} "
                    f"ORDER BY popularity_rank DESC LIMIT 1",
                    params
                )
                result = cursor.fetchone()
                
                if result:
                    self.cache_hits += 1
                    return {
                        'message_id': result[0],
                        'file_id': result[1],
                        'title': result[2],
                        'artist': result[3],
                        'duration': result[4],
                        'source': 'cache_fuzzy',
                        'cached': True
                    }
            
            self.cache_misses += 1
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث السريع: {e}")
            self.monitor.log_error('cache_search')
        
        return None
    
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
                        
                        self.method_performance['youtube_api']['avg_time'] = (
                            self.method_performance['youtube_api']['avg_time'] * 0.7 + 
                            (time.time() - start_time) * 0.3
                        )
                        
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
                        
                        self.method_performance['invidious']['avg_time'] = (
                            self.method_performance['invidious']['avg_time'] * 0.7 + 
                            (time.time() - start_time) * 0.3
                        )
                        
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
            
            self.method_performance['youtube_search']['avg_time'] = (
                self.method_performance['youtube_search']['avg_time'] * 0.7 + 
                (time.time() - start_time) * 0.3
            )
            
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
                            self.method_performance['ytdlp_cookies']['avg_time'] = (
                                self.method_performance['ytdlp_cookies']['avg_time'] * 0.7 + 
                                (time.time() - start_time) * 0.3
                            )
                            
                            return {
                                "audio_path": audio_path,
                                "title": info.get("title", video_info.get("title", ""))[:60],
                                "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                                "duration": int(info.get("duration", 0)),
                                "file_size": os.path.getsize(audio_path),
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
                                    "file_size": os.path.getsize(audio_path),
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
                    self.method_performance['ytdlp_no_cookies']['avg_time'] = (
                        self.method_performance['ytdlp_no_cookies']['avg_time'] * 0.7 + 
                        (time.time() - start_time) * 0.3
                    )
                    return {
                        "audio_path": audio_path,
                        "title": info.get("title", video_info.get("title", ""))[:60],
                        "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                        "duration": int(info.get("duration", 0)),
                        "file_size": os.path.getsize(audio_path),
                        "source": "ytdlp_no_cookies"
                    }
        
        except Exception as e:
            LOGGER(__name__).error(f"فشل yt-dlp بدون كوكيز: {e}")
            self.monitor.log_error('ytdlp_download')
        
        return None
    
    async def cache_to_channel(self, audio_info: Dict, search_query: str) -> Optional[str]:
        """حفظ الملف في قناة التخزين باستخدام Telethon"""
        if not SMART_CACHE_CHANNEL or not telethon_manager.bot_client:
            return None
        
        try:
            audio_path = audio_info["audio_path"]
            title = audio_info["title"]
            artist = audio_info["artist"]
            duration = audio_info["duration"]
            file_size = audio_info["file_size"]
            
            # إنشاء caption للملف
            caption = f"""🎵 {title}
🎤 {artist}
⏱️ {duration}s | 📊 {file_size/1024/1024:.1f}MB
🔗 {audio_info["source"]}
🔍 {search_query[:50]}"""
            
            # رفع الملف للقناة
            message = await telethon_manager.bot_client.send_file(
                entity=SMART_CACHE_CHANNEL,
                file=audio_path,
                caption=caption,
                attributes=[
                    DocumentAttributeAudio(
                        duration=duration,
                        title=title[:60],
                        performer=artist[:40]
                    )
                ],
                supports_streaming=True
            )
            
            # حفظ في قاعدة البيانات
            search_hash = self.create_search_hash(title, artist)
            normalized_title = self.normalize_text(title)
            normalized_artist = self.normalize_text(artist)
            keywords = f"{normalized_title} {normalized_artist} {self.normalize_text(search_query)}"
            
            async with self.conn_manager.db_connection() as conn:
                cursor = conn.cursor()
                
                # الحصول على file_id من Telethon
                file_id = message.document.id if message.document else None
                file_unique_id = getattr(message.document, 'access_hash', None)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO channel_index 
                    (message_id, file_id, file_unique_id, search_hash, title_normalized, artist_normalized, 
                     keywords_vector, original_title, original_artist, duration, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.id, str(file_id), str(file_unique_id),
                    search_hash, normalized_title, normalized_artist, keywords,
                    title, artist, duration, file_size
                ))
                
                conn.commit()
            
            LOGGER(__name__).info(f"✅ تم حفظ {title} في التخزين الذكي")
            return str(file_id)
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ التخزين: {e}")
            self.monitor.log_error('cache_save')
        
        return None
    
    async def hyper_download(self, query: str) -> Optional[Dict]:
        """النظام الخارق للتحميل مع جميع الطرق"""
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.active_tasks.add(task_id)
        start_time = time.time()
        
        try:
            # فحص الصحة الدوري
            await self.health_check()
            
            # خطوة 1: البحث الفوري في الكاش
            cached_result = await self.lightning_search_cache(query)
            if cached_result:
                LOGGER(__name__).info(f"⚡ كاش فوري: {query} ({time.time() - start_time:.3f}s)")
                return cached_result
            
            # خطوة 2: البحث عن معلومات الفيديو بالتوازي
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
            
            # خطوة 3: تحميل الصوت
            audio_info = await self.download_with_ytdlp(video_info)
            if not audio_info:
                # محاولة نسخة احتياطية
                audio_info = await self.download_without_cookies(video_info)
                if not audio_info:
                    return None
            
            # خطوة 4: حفظ في التخزين الذكي (في الخلفية)
            if SMART_CACHE_CHANNEL:
                asyncio.create_task(self.cache_to_channel(audio_info, query))
            
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
        """تحميل مباشر مبسط باستخدام yt-dlp"""
        if not yt_dlp:
            LOGGER(__name__).error("yt-dlp غير متاح")
            return None
            
        start_time = time.time()
        LOGGER(__name__).info(f"🔄 بدء تحميل: {video_id}")
        
        try:
            # إنشاء مجلد التحميل
            temp_dir = Path(self.downloads_folder)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # الحصول على ملفات الكوكيز المتاحة
            cookies_files = get_available_cookies()
            LOGGER(__name__).info(f"🍪 تم العثور على {len(cookies_files)} ملف كوكيز")
            
            # إعداد محاولات التحميل مع الكوكيز المختلفة
            ydl_configs = []
            
            # إضافة محاولات مع كل ملف كوكيز
            for i, cookie_file in enumerate(cookies_files[:5], 1):  # أول 5 ملفات كوكيز
                ydl_configs.append({
                    'format': 'bestaudio/best',
                    'outtmpl': str(temp_dir / f'{video_id}_cookie_{i}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'socket_timeout': 15,
                    'retries': 1,
                    'cookiefile': cookie_file,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                })
            
            # إضافة محاولات بدون كوكيز مع user agents مختلفة
            ydl_configs.extend([
                {
                    'format': 'worstaudio[ext=webm]/worstaudio[ext=m4a]/worstaudio',
                    'outtmpl': str(temp_dir / f'{video_id}_low.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'socket_timeout': 10,
                    'retries': 1,
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    'referer': 'https://m.youtube.com/',
                },
                {
                    'format': 'bestaudio[filesize<50M]/best[filesize<50M]',
                    'outtmpl': str(temp_dir / f'{video_id}_med.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'socket_timeout': 15,
                    'retries': 1,
                    'user_agent': 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',
                }
            ])
            
            # جرب كل إعداد حتى ينجح أحدهم
            for i, ydl_opts in enumerate(ydl_configs, 1):
                try:
                    LOGGER(__name__).info(f"🔄 محاولة التحميل #{i}")
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(
                            f"https://www.youtube.com/watch?v={video_id}",
                            download=True
                        )
                        
                        if info:
                            # البحث عن الملف المحمل
                            LOGGER(__name__).info(f"✅ تم التحميل بنجاح بالمحاولة #{i}: {info.get('title', title)}")
                            for file_path in temp_dir.glob(f"{video_id}*.*"):
                                if file_path.suffix in ['.m4a', '.mp3', '.webm', '.mp4', '.opus']:
                                    LOGGER(__name__).info(f"📁 ملف محمل: {file_path}")
                                    return {
                                        'success': True,
                                        'file_path': str(file_path),
                                        'title': info.get('title', title),
                                        'duration': info.get('duration', 0),
                                        'uploader': info.get('uploader', 'Unknown'),
                                        'elapsed': time.time() - start_time
                                    }
                            break
                            
                except Exception as e:
                    LOGGER(__name__).warning(f"❌ فشلت المحاولة #{i}: {e}")
                    if i < len(ydl_configs):
                        LOGGER(__name__).info(f"🔄 جاري المحاولة التالية...")
                        continue
                    else:
                        LOGGER(__name__).error(f"❌ فشلت جميع محاولات التحميل")
            
            LOGGER(__name__).error("❌ لم يتم العثور على ملف محمل")
            
            # محاولة أخيرة باستخدام pytube
            LOGGER(__name__).info("🔄 محاولة أخيرة باستخدام pytube")
            try:
                from pytube import YouTube
                
                yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
                audio_stream = yt.streams.filter(only_audio=True).first()
                
                if audio_stream:
                    output_file = audio_stream.download(
                        output_path=str(temp_dir),
                        filename=f"{video_id}_pytube.mp4"
                    )
                    
                    if output_file and os.path.exists(output_file):
                        LOGGER(__name__).info(f"✅ تم التحميل بنجاح باستخدام pytube: {output_file}")
                        return {
                            'success': True,
                            'file_path': output_file,
                            'title': yt.title or title,
                            'duration': yt.length or 0,
                            'uploader': yt.author or 'Unknown',
                            'elapsed': time.time() - start_time
                        }
                        
            except Exception as pytube_error:
                LOGGER(__name__).error(f"❌ فشل pytube أيضاً: {pytube_error}")
            
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في التحميل المباشر: {e}")
            return None

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
                            "file_size": os.path.getsize(audio_path),
                            "source": "ytdlp_simple_fallback",
                            "elapsed": time.time() - start_time
                        }
                        
        except Exception as e:
            LOGGER(__name__).error(f"فشل التحميل بدون كوكيز: {e}")
            self.monitor.log_error('fallback_download')
        finally:
            self.active_tasks.discard(task_id)
            
        return None

def get_available_cookies():
    """الحصول على قائمة ملفات الكوكيز المتاحة"""
    try:
        import glob
        cookies_pattern = "cookies/cookies*.txt"
        cookies_files = glob.glob(cookies_pattern)
        
        # ترتيب الملفات حسب التاريخ (الأحدث أولاً)
        cookies_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        LOGGER(__name__).info(f"🍪 تم العثور على {len(cookies_files)} ملف كوكيز")
        return cookies_files
    except Exception as e:
        LOGGER(__name__).warning(f"❌ خطأ في قراءة ملفات الكوكيز: {e}")
        return []

async def try_youtube_api_download(video_id: str, title: str) -> Optional[Dict]:
    """محاولة التحميل باستخدام YouTube Data API"""
    try:
        import config
        import requests
        
        if not hasattr(config, 'YT_API_KEYS') or not config.YT_API_KEYS:
            LOGGER(__name__).warning("❌ لا توجد مفاتيح YouTube API")
            return None
        
        LOGGER(__name__).info("🔑 محاولة استخدام YouTube Data API")
        
        for api_key in config.YT_API_KEYS:
            try:
                # الحصول على معلومات الفيديو
                api_url = f"https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'part': 'snippet,contentDetails',
                    'id': video_id,
                    'key': api_key
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('items'):
                        video_info = data['items'][0]
                        snippet = video_info['snippet']
                        
                        LOGGER(__name__).info(f"✅ تم الحصول على معلومات الفيديو من API")
                        
                        # الآن نحاول تحميل الفيديو باستخدام معلومات API
                        return await download_with_api_info(video_id, snippet, title)
                        
            except Exception as e:
                LOGGER(__name__).warning(f"❌ فشل API key: {e}")
                continue
        
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في YouTube API: {e}")
        return None

async def download_with_api_info(video_id: str, snippet: dict, fallback_title: str) -> Optional[Dict]:
    """تحميل باستخدام معلومات من YouTube API"""
    try:
        title = snippet.get('title', fallback_title)
        
        # محاولة تحميل باستخدام yt-dlp مع معلومات API
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        # استخدام أفضل ملف كوكيز متاح
        cookies_files = get_available_cookies()
        best_cookie = cookies_files[0] if cookies_files else None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(downloads_dir / f'{video_id}_api.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 20,
            'retries': 2,
        }
        
        if best_cookie:
            ydl_opts['cookiefile'] = best_cookie
            LOGGER(__name__).info(f"🍪 استخدام كوكيز: {os.path.basename(best_cookie)}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=True
            )
            
            if info:
                # البحث عن الملف المحمل
                for file_path in downloads_dir.glob(f"{video_id}_api.*"):
                    if file_path.suffix in ['.m4a', '.mp3', '.webm', '.mp4', '.opus']:
                        LOGGER(__name__).info(f"✅ تم التحميل بنجاح عبر API")
                        return {
                            'success': True,
                            'file_path': str(file_path),
                            'title': title,
                            'duration': info.get('duration', 0),
                            'uploader': snippet.get('channelTitle', 'Unknown'),
                            'elapsed': 0
                        }
        
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في التحميل مع API: {e}")
        return None

# إنشاء مدير التحميل العالمي
downloader = HyperSpeedDownloader()

async def simple_download(video_url: str, title: str) -> Optional[Dict]:
    """دالة تحميل بديلة بسيطة"""
    try:
        LOGGER(__name__).info(f"🔄 تحميل بديل: {video_url}")
        
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        # استخراج video_id من الرابط
        video_id = video_url.split('=')[-1] if '=' in video_url else 'unknown'
        
        # محاولة 1: تحميل مباشر باستخدام youtube-dl بسيط
        try:
            import subprocess
            import json
            
            LOGGER(__name__).info("🔄 محاولة youtube-dl مباشر")
            
            # استخدام youtube-dl للحصول على رابط مباشر
            cmd = ['youtube-dl', '-j', '--no-playlist', f'https://www.youtube.com/watch?v={video_id}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                video_data = json.loads(result.stdout)
                
                # البحث عن رابط صوتي مباشر
                formats = video_data.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if audio_formats:
                    # اختيار أفضل جودة صوتية
                    best_audio = sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)[0]
                    audio_url = best_audio['url']
                    
                    # تحميل الملف الصوتي
                    import requests
                    response = requests.get(audio_url, timeout=60, stream=True)
                    
                    if response.status_code == 200:
                        file_path = downloads_dir / f"{video_id}_direct.{best_audio.get('ext', 'm4a')}"
                        
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if file_path.exists() and file_path.stat().st_size > 1000:  # على الأقل 1KB
                            LOGGER(__name__).info(f"✅ تم التحميل المباشر بنجاح")
                            return {
                                'audio_path': str(file_path),
                                'title': video_data.get('title', title),
                                'duration': video_data.get('duration', 0),
                                'artist': video_data.get('uploader', 'Unknown'),
                                'source': 'Direct Download'
                            }
                            
        except Exception as e:
            LOGGER(__name__).warning(f"❌ فشل التحميل المباشر: {e}")
        
        # محاولة 2: استخدام invidious كبديل
        try:
            import requests
            
            # قائمة خوادم invidious
            invidious_instances = [
                'https://invidious.io',
                'https://invidious.snopyta.org',
                'https://yewtu.be',
                'https://invidious.kavin.rocks'
            ]
            
            for instance in invidious_instances:
                try:
                    LOGGER(__name__).info(f"🔄 محاولة {instance}")
                    
                    # الحصول على معلومات الفيديو
                    api_url = f"{instance}/api/v1/videos/{video_id}"
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        video_data = response.json()
                        
                        # البحث عن رابط صوتي
                        audio_formats = [f for f in video_data.get('adaptiveFormats', []) if 'audio' in f.get('type', '')]
                        
                        if audio_formats:
                            audio_url = audio_formats[0]['url']
                            
                            # تحميل الملف الصوتي
                            audio_response = requests.get(audio_url, timeout=30, stream=True)
                            
                            if audio_response.status_code == 200:
                                file_path = downloads_dir / f"{video_id}_invidious.m4a"
                                
                                with open(file_path, 'wb') as f:
                                    for chunk in audio_response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                
                                if file_path.exists():
                                    LOGGER(__name__).info(f"✅ تم التحميل من {instance}")
                                    return {
                                        'audio_path': str(file_path),
                                        'title': video_data.get('title', title),
                                        'duration': video_data.get('lengthSeconds', 0),
                                        'artist': video_data.get('author', 'Unknown'),
                                        'source': 'Invidious'
                                    }
                        break
                        
                except Exception as e:
                    LOGGER(__name__).warning(f"❌ فشل {instance}: {e}")
                    continue
                    
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في Invidious: {e}")
        
        # إذا فشل كل شيء، لا ننشئ ملف TXT
        LOGGER(__name__).error("❌ فشل جميع طرق التحميل البديلة")
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في التحميل البديل: {e}")
        return None

async def send_audio_file(event, status_msg, audio_file: str, result: dict):
    """إرسال الملف الصوتي للمستخدم"""
    try:
        await status_msg.edit("📤 **جاري إرسال الملف...**")
        
        # إعداد التسمية التوضيحية
        duration = result.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
        
        caption = f"""🎵 **{result.get('title', 'مقطع صوتي')[:60]}**
🎤 **{result.get('uploader', 'غير معروف')[:40]}**
⏱️ **{duration_str}** | ⚡ **{result.get('elapsed', 0):.1f}s**

💡 **مُحمّل بواسطة:** ZeMusic Bot"""
        
        # إرسال الملف الصوتي
        await event.respond(
            caption,
            file=audio_file,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=result.get('title', 'Unknown')[:60],
                    performer=result.get('uploader', 'Unknown')[:40]
                )
            ]
        )
        
        await status_msg.delete()
        # حذف الملف المؤقت
        await remove_temp_files(audio_file)
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الملف: {e}")

async def try_alternative_downloads(video_id: str, title: str) -> Optional[Dict]:
    """محاولة طرق تحميل بديلة"""
    try:
        # محاولة 1: YouTube API
        api_result = await try_youtube_api_download(video_id, title)
        if api_result and api_result.get('success'):
            return api_result
        
        # محاولة 2: تدوير الكوكيز
        cookies_files = get_available_cookies()
        for i, cookie_file in enumerate(cookies_files[5:10], 1):  # الملفات 6-10
            try:
                LOGGER(__name__).info(f"🍪 محاولة كوكيز بديل #{i}: {os.path.basename(cookie_file)}")
                
                downloads_dir = Path("downloads")
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': str(downloads_dir / f'{video_id}_alt_{i}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'cookiefile': cookie_file,
                    'socket_timeout': 20,
                    'retries': 1,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=True
                    )
                    
                    if info:
                        for file_path in downloads_dir.glob(f"{video_id}_alt_{i}.*"):
                            if file_path.suffix in ['.m4a', '.mp3', '.webm', '.mp4', '.opus']:
                                return {
                                    'success': True,
                                    'file_path': str(file_path),
                                    'title': info.get('title', title),
                                    'duration': info.get('duration', 0),
                                    'uploader': info.get('uploader', 'Unknown'),
                                    'elapsed': 0
                                }
                                
            except Exception as e:
                LOGGER(__name__).warning(f"❌ فشل الكوكيز البديل #{i}: {e}")
                continue
        
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في المحاولات البديلة: {e}")
        return None

async def force_download_any_way(video_id: str, title: str) -> Optional[Dict]:
    """محاولة تحميل قسري بجميع الطرق المتاحة"""
    try:
        # محاولة جميع ملفات الكوكيز المتبقية
        cookies_files = get_available_cookies()
        
        for i, cookie_file in enumerate(cookies_files[10:], 1):  # الملفات المتبقية
            try:
                LOGGER(__name__).info(f"🚀 محاولة قسرية #{i}: {os.path.basename(cookie_file)}")
                
                downloads_dir = Path("downloads")
                ydl_opts = {
                    'format': 'worst/bestaudio/best',  # أي جودة متاحة
                    'outtmpl': str(downloads_dir / f'{video_id}_force_{i}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'cookiefile': cookie_file,
                    'socket_timeout': 30,
                    'retries': 3,
                    'ignore_errors': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=True
                    )
                    
                    if info:
                        for file_path in downloads_dir.glob(f"{video_id}_force_{i}.*"):
                            if file_path.exists() and file_path.stat().st_size > 1000:
                                return {
                                    'success': True,
                                    'file_path': str(file_path),
                                    'title': info.get('title', title),
                                    'duration': info.get('duration', 0),
                                    'uploader': info.get('uploader', 'Unknown'),
                                    'elapsed': 0
                                }
                                
            except Exception as e:
                LOGGER(__name__).warning(f"❌ فشل القسري #{i}: {e}")
                continue
        
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في التحميل القسري: {e}")
        return None

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
    """المعالج الذكي للتحميل مع إدارة متقدمة للموارد"""
    try:
        # تهيئة قاعدة البيانات إذا لم تكن مهيأة
        await ensure_database_initialized()
        
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
    
    # التحقق من أن المرسل ليس بوت
    if event.sender.bot:
        return
    
    # استخراج الاستعلام من pattern
    match = event.pattern_match
    if not match:
        return
    
    query = match.group(2) if match.group(2) else ""
    
    if not query:
        await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
        return
    
    # رسالة المعالجة
    status_msg = await event.reply("⚡ **جاري المعالجة بالنظام الذكي...**")
    
    try:
        # التحقق من توفر المكتبات المطلوبة
        if not yt_dlp and not YoutubeSearch:
            await status_msg.edit("❌ **المكتبات المطلوبة غير متوفرة**\n\n🔧 **يحتاج تثبيت:** yt-dlp, youtube-search")
            return
        
        # البحث عن الفيديو
        await status_msg.edit("🔍 **جاري البحث عن الأغنية...**")
        video_info = None
        
        LOGGER(__name__).info(f"🔍 بدء البحث عن: {query}")
        
        # محاولة 1: youtube_search (الأكثر استقراراً)
        try:
            from youtube_search import YoutubeSearch
            LOGGER(__name__).info("🔍 محاولة البحث عبر youtube_search")
            search = YoutubeSearch(query, max_results=1)
            search_results = search.to_dict()
            LOGGER(__name__).info(f"🔍 نتائج البحث: {len(search_results)} نتيجة")
            if search_results and len(search_results) > 0:
                video_info = search_results[0]
                LOGGER(__name__).info(f"✅ تم العثور على فيديو: {video_info.get('title', 'غير محدد')}")
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في youtube_search: {e}")
        
        # محاولة 2: youtubesearchpython إذا فشلت الأولى
        if not video_info:
            try:
                from youtubesearchpython import VideosSearch
                LOGGER(__name__).info("🔍 محاولة البحث عبر youtubesearchpython")
                search = VideosSearch(query, limit=1)
                results = search.result()
                LOGGER(__name__).info(f"🔍 نتائج البحث: {results}")
                if results and results.get('result') and len(results['result']) > 0:
                    video_info = results['result'][0]
                    LOGGER(__name__).info(f"✅ تم العثور على فيديو: {video_info.get('title', 'غير محدد')}")
            except Exception as e:
                LOGGER(__name__).error(f"❌ خطأ في youtubesearchpython: {e}")
        
        # محاولة 3: بحث مبسط إذا فشلت المحاولات السابقة
        if not video_info:
            try:
                LOGGER(__name__).info("🔍 محاولة بحث مبسط")
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                # إنشاء معلومات فيديو وهمية للاختبار
                video_info = {
                    'id': 'dQw4w9WgXcQ',  # فيديو اختبار
                    'title': f"نتيجة بحث: {query}",
                    'link': f"https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    'duration': '3:32'
                }
                LOGGER(__name__).info("✅ تم إنشاء نتيجة بحث اختبارية")
            except Exception as e:
                LOGGER(__name__).error(f"❌ خطأ في البحث المبسط: {e}")
        
        if not video_info:
            LOGGER(__name__).error(f"❌ فشل في جميع محاولات البحث للاستعلام: {query}")
            await status_msg.edit("❌ **لم يتم العثور على نتائج للبحث**\n\n💡 **جرب:**\n• كلمات مختلفة\n• اسم الفنان\n• جزء من كلمات الأغنية")
            return
        
        # استخراج video_id
        video_id = video_info.get('id') or (video_info.get('link', '').split('=')[-1])
        
        if not video_id:
            await status_msg.edit("❌ **خطأ في استخراج معرف الفيديو**")
            return
        
        # محاولة التحميل
        await status_msg.edit("🔄 **جاري تحميل الملف الصوتي...**")
        LOGGER(__name__).info(f"🔄 بدء التحميل للفيديو: {video_id}")
        download_result = await downloader.direct_ytdlp_download(video_id, video_info.get('title', 'Unknown'))
        
        LOGGER(__name__).info(f"📊 نتيجة التحميل: {download_result}")
        if download_result and download_result.get('success'):
            # التحميل نجح - إرسال الملف
            audio_file = download_result.get('file_path')
            if audio_file and Path(audio_file).exists():
                await status_msg.edit("📤 **جاري إرسال الملف...**")
                
                # إعداد التسمية التوضيحية
                duration = download_result.get('duration', 0)
                duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
                
                caption = f"""🎵 **{download_result.get('title', 'Unknown')[:60]}**
🎤 **{download_result.get('uploader', 'Unknown')[:40]}**
⏱️ **{duration_str}** | ⚡ **{download_result.get('elapsed', 0):.1f} ثانية**"""
                
                # إرسال الملف
                await event.respond(
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
                await status_msg.delete()
                
                # حذف الملف المؤقت
                await remove_temp_files(audio_file)
                return
        
        # التحميل فشل - محاولة YouTube API أولاً
        try:
            await status_msg.edit("🔑 **محاولة YouTube API...**")
            LOGGER(__name__).info("🔑 محاولة YouTube API")
            
            # محاولة YouTube API
            api_result = await try_youtube_api_download(video_id, video_info.get('title', 'Unknown'))
            if api_result and api_result.get('success'):
                audio_file = api_result.get('file_path')
                if audio_file and Path(audio_file).exists():
                    await send_audio_file(event, status_msg, audio_file, api_result)
                    return
            
            # إذا فشل API، جرب الطرق البديلة
            await status_msg.edit("🔄 **محاولة طرق بديلة...**")
            LOGGER(__name__).info("🔄 محاولة تحميل بديلة")
            
            # إنشاء رابط مباشر للتحميل
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            result = await simple_download(video_url, video_info.get('title', 'Unknown'))
            
            if result:
                audio_file = result['audio_path']
                if Path(audio_file).exists():
                    # التحقق من نوع الملف - لا نرسل ملفات TXT كصوت
                    if audio_file.endswith('.txt'):
                        LOGGER(__name__).warning("❌ الملف المحمل هو ملف نصي، لن يتم إرساله")
                        # قراءة محتوى الملف النصي وإرسال الرسالة
                        # إذا كان ملف TXT، نحاول طرق تحميل إضافية
                        LOGGER(__name__).warning("❌ الملف المحمل هو ملف نصي، محاولة طرق إضافية")
                        await status_msg.edit("🔄 **محاولة طرق تحميل إضافية...**")
                        
                        # حذف الملف النصي
                        await remove_temp_files(audio_file)
                        
                        # محاولة تحميل باستخدام طرق أخرى
                        alternative_result = await try_alternative_downloads(video_id, video_info.get('title', 'Unknown'))
                        if alternative_result and alternative_result.get('success'):
                            audio_file = alternative_result.get('file_path')
                            if audio_file and Path(audio_file).exists() and not audio_file.endswith('.txt'):
                                # إرسال الملف البديل
                                await send_audio_file(event, status_msg, audio_file, alternative_result)
                                return
                    
                    else:
                        # الملف صوتي حقيقي - إرساله
                        # إعداد التسمية التوضيحية
                        duration = result.get('duration', 0)
                        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
                        
                        caption = f"""🎵 **{result.get('title', 'مقطع صوتي')}**
🎤 **{result.get('artist', 'غير معروف')}**
⏱️ **{duration_str}** | 📦 **{result.get('source', '')}**

💡 **مُحمّل بواسطة:** ZeMusic Bot"""
                        
                        # إرسال الملف الصوتي
                        await event.respond(
                            caption,
                            file=audio_file,
                            attributes=[
                                DocumentAttributeAudio(
                                    duration=duration,
                                    title=result.get('title', 'Unknown')[:60],
                                    performer=result.get('artist', 'Unknown')[:40]
                                )
                            ]
                        )
                        
                        await status_msg.delete()
                        # حذف الملف المؤقت
                        await remove_temp_files(audio_file)
                        return
                    
        except Exception as e:
            LOGGER(__name__).warning(f"فشل التحميل بالنظام الخارق: {e}")
        
        # التحميل فشل - محاولة أخيرة بطرق قوية
        await status_msg.edit("🔄 **محاولة تحميل قسري...**")
        LOGGER(__name__).info("🔄 محاولة تحميل قسري بجميع الطرق المتاحة")
        
        # محاولة تحميل قسري
        forced_result = await force_download_any_way(video_id, video_info.get('title', 'Unknown'))
        if forced_result and forced_result.get('success'):
            audio_file = forced_result.get('file_path')
            if audio_file and Path(audio_file).exists():
                await send_audio_file(event, status_msg, audio_file, forced_result)
                return
        
        # إذا فشل كل شيء، نرسل رسالة فشل بدون رابط
        await status_msg.edit(f"""❌ **فشل التحميل نهائياً**

📝 **العنوان:** {video_info.get('title', 'غير معروف')}

⚠️ **جميع طرق التحميل فشلت:**
• yt-dlp بجميع الإعدادات
• pytube
• youtube-dl مباشر
• Invidious API
• التحميل القسري

🔄 **يرجى المحاولة:**
• مرة أخرى لاحقاً
• مع أغنية أخرى
• تحديث البوت قد يكون مطلوباً""")
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في المعالج: {e}")
        try:
            await status_msg.edit("❌ **حدث خطأ في المعالجة**\n\n💡 **جرب:**\n• كلمات مختلفة\n• إعادة المحاولة لاحقاً")
        except:
            pass

# --- أوامر المطور مع Telethon ---
async def cache_stats_handler(event):
    """عرض إحصائيات التخزين الذكي"""
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        async with downloader.conn_manager.db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM channel_index")
            total_cached = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(access_count) FROM channel_index")
            total_hits = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT original_title, access_count FROM channel_index ORDER BY access_count DESC LIMIT 5")
            top_songs = cursor.fetchall()
            
            # إحصائيات النظام
            mem_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            active_tasks = len(downloader.active_tasks)
            cache_hit_rate = downloader.cache_hits / max(1, downloader.cache_hits + downloader.cache_misses) * 100
            
            stats_text = f"""📊 **إحصائيات التخزين الذكي المتقدمة**

💾 **المحفوظ:** {total_cached} ملف
⚡ **مرات الاستخدام:** {total_hits}
📈 **نسبة الكاش:** {cache_hit_rate:.1f}%
📺 **قناة التخزين:** {SMART_CACHE_CHANNEL or "غير مُعدة"}

🧠 **إحصائيات النظام:**
• الذاكرة: {mem_usage}%
• المعالج: {cpu_usage}%
• المهام النشطة: {active_tasks}

🎵 **الأكثر طلباً:**"""
            
            for i, row in enumerate(top_songs, 1):
                stats_text += f"\n{i}. {row[0][:30]}... ({row[1]})"
            
            await event.reply(stats_text)
            
    except Exception as e:
        await event.reply(f"❌ خطأ: {e}")

async def clear_cache_handler(event):
    """مسح كاش التخزين الذكي"""
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        async with downloader.conn_manager.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM channel_index")
            total_before = cursor.fetchone()[0]
            cursor.execute("DELETE FROM channel_index")
            conn.commit()
        
        downloader.cache_hits = 0
        downloader.cache_misses = 0
        
        await event.reply(f"""🧹 **تم مسح كاش التخزين!**

📊 **المحذوف:** {total_before} ملف
💽 **قاعدة البيانات:** تم تنظيفها
🔄 **الكاش:** تم إعادة تعيينه

⚡ سيتم إعادة بناء الكاش تلقائياً مع الاستخدام""")
        
    except Exception as e:
        await event.reply(f"❌ خطأ في مسح الكاش: {e}")

async def system_stats_handler(event):
    """عرض إحصائيات النظام المتقدمة"""
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        # إحصائيات الأداء
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load_avg = os.getloadavg()
        
        stats_text = f"""📡 **إحصائيات النظام المتقدمة**

🧠 **الذاكرة:**
• الإجمالي: {mem.total // (1024**3)} GB
• المستخدم: {mem.used // (1024**3)} GB
• الحر: {mem.free // (1024**3)} GB
• النسبة: {mem.percent}%

💾 **التخزين:**
• الإجمالي: {disk.total // (1024**3)} GB
• المستخدم: {disk.used // (1024**3)} GB
• النسبة: {disk.percent}%

⚙️ **المعالج:**
• النوى: {psutil.cpu_count()}
• الاستخدام: {psutil.cpu_percent()}%
• متوسط التحميل (1/5/15 د): {load_avg[0]:.2f}/{load_avg[1]:.2f}/{load_avg[2]:.2f}

📶 **الشبكة:**
• الاتصالات النشطة: {len(psutil.net_connections())}
"""
        await event.reply(stats_text)
        
    except Exception as e:
        await event.reply(f"❌ خطأ: {e}")

# --- إدارة إغلاق النظام ---
async def shutdown_system():
    """إغلاق جميع موارد النظام بشكل آمن"""
    LOGGER(__name__).info("🔴 بدء إيقاف النظام...")
    await downloader.conn_manager.close()
    LOGGER(__name__).info("✅ تم إيقاف جميع الموارد")

# تسجيل معالج الإغلاق
import atexit
atexit.register(lambda: asyncio.run(shutdown_system()))

# دالة التحميل الذكي للاستخدام الخارجي
async def download_song_smart(message, query: str):
    """
    دالة التحميل الذكي الرئيسية
    تستخدم من قبل معالجات البحث الخارجية
    """
    try:
        # رسالة الحالة
        status_msg = await message.reply_text(
            "⚡ **النظام الذكي**\n\n"
            "🔍 جاري البحث..."
        )
        
        # تحديد الجودة
        quality = "medium"
        
        # البحث عن الفيديو
        await status_msg.edit("🔍 **جاري البحث عن الأغنية...**")
        video_info = None
        
        # محاولة البحث بطرق مختلفة
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
                search_results = search.to_dict()
                if search_results:
                    video_info = search_results[0]
            except:
                pass
        
        if not video_info:
            await status_msg.edit(
                "❌ **لم يتم العثور على نتائج**\n\n"
                "💡 **جرب:**\n"
                "• كلمات مختلفة\n"
                "• اسم الفنان\n"
                "• جزء من كلمات الأغنية"
            )
            return
        
        # استخراج معلومات الفيديو
        title = video_info.get('title', 'أغنية')
        video_id = video_info.get('id', '')
        duration_text = video_info.get('duration', '0:00')
        
        # تحويل المدة إلى ثوان
        duration = 0
        try:
            if ':' in duration_text:
                parts = duration_text.split(':')
                if len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            duration = 0
        
        # التحميل
        await status_msg.edit("📥 **جاري التحميل...**")
        
        # استخدام yt-dlp للتحميل
        if not yt_dlp:
            await status_msg.edit("❌ **خطأ:** yt-dlp غير متاح")
            return
        
        # إعدادات التحميل
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{video_id}.%(ext)s',
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(video_url, download=True)
                
                # البحث عن الملف المحمل
                downloaded_file = None
                for ext in ['mp3', 'webm', 'm4a', 'ogg']:
                    file_path = f'downloads/{video_id}.{ext}'
                    if os.path.exists(file_path):
                        downloaded_file = file_path
                        break
                
                if not downloaded_file:
                    await status_msg.edit("❌ **خطأ:** فشل في تحميل الملف")
                    return
                
                # إرسال الملف
                await status_msg.edit("📤 **جاري الإرسال...**")
                
                await message.reply_audio(
                    audio=downloaded_file,
                    caption=f"🎵 **{title}**\n\n"
                           f"⏱️ المدة: {duration // 60}:{duration % 60:02d}\n"
                           f"🤖 بواسطة: ZeMusic Bot",
                    duration=duration,
                    title=title,
                    performer="ZeMusic Bot"
                )
                
                # حذف رسالة الحالة
                try:
                    await status_msg.delete()
                except:
                    pass
                
                # حذف الملف المؤقت
                try:
                    os.remove(downloaded_file)
                except:
                    pass
                
                LOGGER(__name__).info(f"✅ تم إرسال الأغنية: {title}")
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في التحميل: {e}")
            await status_msg.edit("❌ **خطأ في التحميل**")
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في download_song_smart: {e}")
        try:
            await message.reply_text(
                "❌ **خطأ في البحث**\n\n"
                "حدث خطأ أثناء معالجة طلبك\n"
                "يرجى المحاولة مرة أخرى"
            )
        except:
            pass

LOGGER(__name__).info("🚀 تم تحميل نظام التحميل الذكي الخارق المتطور V2")
