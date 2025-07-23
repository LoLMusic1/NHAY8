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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from itertools import cycle
from collections import defaultdict, deque
from asyncio import Semaphore
import threading
import aiohttp
import aiofiles
from telethon.tl.types import DocumentAttributeAudio
from pathlib import Path
import uvloop
import psutil
import random
import string
import atexit
from contextlib import asynccontextmanager
import orjson

# تطبيق UVLoop لتحسين أداء asyncio

def get_audio_duration(file_path: str) -> int:
    """الحصول على مدة الملف الصوتي بالثواني"""
    try:
        if not os.path.exists(file_path):
            return 0
            
        # محاولة استخدام yt-dlp للحصول على المعلومات
        if yt_dlp:
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(file_path, download=False)
                    duration = info.get('duration', 0)
                    if duration and duration > 0:
                        return int(duration)
            except:
                pass
        
        # محاولة استخدام ffprobe
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return int(float(result.stdout.strip()))
        except:
            pass
            
        # تقدير تقريبي بناءً على حجم الملف (للملفات الصوتية)
        try:
            file_size = os.path.getsize(file_path)
            # تقدير: 128kbps = 16KB/s تقريباً
            estimated_duration = file_size // 16000
            return max(1, estimated_duration)
        except:
            return 0
            
    except Exception as e:
        LOGGER.warning(f"⚠️ خطأ في الحصول على مدة الصوت: {e}")
        return 0
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# استيراد المكتبات مع معالجة الأخطاء
try:
    import yt_dlp
except ImportError:
    yt_dlp = None
    
try:
    from youtube_search import YoutubeSearch
    YOUTUBE_SEARCH_AVAILABLE = True
except ImportError:
    YoutubeSearch = None
    YOUTUBE_SEARCH_AVAILABLE = False

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
DATABASE_PATH = "zemusic.db"
DB_FILE = DATABASE_PATH  # توحيد أسماء قواعد البيانات

def normalize_arabic_text(text: str) -> str:
    """تطبيع النص العربي للبحث المحسن"""
    if not text:
        return ""
    
    # إزالة التشكيل والرموز الخاصة
    import re
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)  # إزالة التشكيل
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)  # الاحتفاظ بالعربية والإنجليزية فقط
    text = re.sub(r'\s+', ' ', text).strip()  # إزالة المسافات الزائدة
    return text

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
# DB_FILE تم تعريفه في الأعلى

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
        try:
            if self._session_pool:
                for session in self._session_pool:
                    if session and not session.closed:
                        await session.close()
            if self._executor_pool:
                self._executor_pool.shutdown(wait=True)
            LOGGER(__name__).info("🔌 تم إغلاق جميع موارد الاتصال")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إغلاق الموارد: {e}")

# ================================================================
#                 نظام التحميل الذكي الخارق
# ================================================================
class HyperSpeedDownloader:
    """نسخة مبسطة من نظام التحميل"""
    
    def __init__(self):
        self.downloads_folder = "downloads"
        os.makedirs(self.downloads_folder, exist_ok=True)
        
        # إعداد المتغيرات المطلوبة
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_tasks = set()
        self.last_health_check = time.time()
        
        # إعداد إحصائيات الأداء
        self.method_performance = {
            'youtube_api': {'avg_time': 0},
            'invidious': {'avg_time': 0},
            'youtube_search': {'avg_time': 0},
            'ytdlp_cookies': {'avg_time': 0},
            'ytdlp_no_cookies': {'avg_time': 0}
        }
        
        # إعداد مدير الاتصالات
        try:
            self.conn_manager = ConnectionManager()
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في تهيئة مدير الاتصالات: {e}")
            self.conn_manager = None
        
        # تسجيل بدء التشغيل
        LOGGER(__name__).info("🚀 بدء تشغيل نظام التحميل المحسن")
    
    async def search_in_smart_cache(self, query: str) -> Optional[Dict]:
        """البحث في التخزين الذكي مع آلية متقدمة"""
        try:
            # البحث في قاعدة البيانات أولاً
            normalized_query = normalize_arabic_text(query)
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # البحث بالعنوان والفنان
            cursor.execute("""
                SELECT video_id, title, artist, duration, file_path, thumb, message_id, keywords
                FROM cached_audio 
                WHERE LOWER(title) LIKE ? OR LOWER(artist) LIKE ? OR LOWER(keywords) LIKE ?
                ORDER BY created_at DESC LIMIT 5
            """, (f'%{normalized_query.lower()}%', f'%{normalized_query.lower()}%', f'%{normalized_query.lower()}%'))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                result = results[0]  # أخذ أول نتيجة
                self.cache_hits += 1
                return {
                    "video_id": result[0],
                    "title": result[1],
                    "artist": result[2],
                    "duration": result[3],
                    "file_path": result[4],
                    "thumb": result[5],
                    "message_id": result[6],
                    "source": "smart_cache"
                }
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث السريع: {e}")
            self.cache_misses += 1
            return None
    
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
            # self.monitor.log_error('cache_search')
        
        return None
    
    async def youtube_api_search(self, query: str) -> Optional[Dict]:
        """البحث عبر YouTube Data API مع تحسينات الأداء"""
        if not API_KEYS_CYCLE:
            return None
        
        session = await self.conn_manager.get_session()
        start_time = time.time()
        
        try:
            for attempt in range(len(YT_API_KEYS)):
                key = next(API_KEYS_CYCLE)
                LOGGER(__name__).info(f"🔑 محاولة YouTube API - المحاولة {attempt + 1}")
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
                            error_text = await resp.text()
                            LOGGER(__name__).warning(f"YouTube API خطأ {resp.status}: {error_text[:100]}")
                            continue
                        
                        data = await resp.json()
                        items = data.get("items", [])
                        if not items:
                            LOGGER(__name__).warning(f"YouTube API: لا توجد نتائج لـ {query}")
                            continue
                        
                        item = items[0]
                        video_id = item["id"]["videoId"]
                        snippet = item["snippet"]
                        title = snippet.get("title", "")[:60]
                        
                        LOGGER(__name__).info(f"✅ YouTube API نجح: {title[:30]}...")
                        
                        self.method_performance['youtube_api']['avg_time'] = (
                            self.method_performance['youtube_api']['avg_time'] * 0.7 + 
                            (time.time() - start_time) * 0.3
                        )
                        
                        return {
                            "video_id": video_id,
                            "title": title,
                            "artist": snippet.get("channelTitle", "Unknown"),
                            "thumb": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "source": "youtube_api"
                        }
                
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
        
        except Exception as e:
            LOGGER(__name__).warning(f"فشل YouTube API: {e}")
            # self.monitor.log_error('youtube_api')
        
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
            # self.monitor.log_error('invidious')
        
        return None
    
    async def youtube_search_simple(self, query: str) -> Optional[Dict]:
        """البحث عبر youtube_search مع معالجة محسنة"""
        if not YoutubeSearch:
            return None
        
        start_time = time.time()
            
        try:
            # التحقق من توفر مكتبة البحث
            if not YoutubeSearch:
                LOGGER(__name__).warning(f"YouTube Search غير متاح")
                return None
            
            # استخدام youtube_search
            LOGGER(__name__).info(f"🔍 بدء البحث في YouTube Search: {query}")
            search = YoutubeSearch(query, max_results=1)
            results = search.to_dict()
            
            LOGGER(__name__).info(f"📊 عدد النتائج: {len(results) if results else 0}")
            
            if not results:
                LOGGER(__name__).warning(f"❌ لا توجد نتائج للبحث: {query}")
                return None
                
            result = results[0]
            LOGGER(__name__).info(f"📝 النتيجة الأولى: {result.get('title', 'Unknown')[:30]}...")
            
            # استخراج معرف الفيديو
            video_id = result.get('id', '')
            
            # إذا لم يكن المعرف موجود، حاول استخراجه من الرابط
            if not video_id:
                url_suffix = result.get('url_suffix', '')
                link = result.get('link', '')
                
                if url_suffix and 'watch?v=' in url_suffix:
                    video_id = url_suffix.split('watch?v=')[1].split('&')[0]
                elif link and 'watch?v=' in link:
                    video_id = link.split('watch?v=')[1].split('&')[0]
            
            LOGGER(__name__).info(f"🔗 URL Suffix: {result.get('url_suffix', 'Unknown')}")
            LOGGER(__name__).info(f"🆔 معرف الفيديو المستخرج: {video_id}")
            title = result.get('title', 'Unknown Title')
            artist = result.get('channel', 'Unknown Artist')
            duration_text = result.get('duration', '0:00')
            thumb = result.get('thumbnails', [None])[0] if result.get('thumbnails') else None
            
            LOGGER(__name__).info(f"🆔 معرف الفيديو: {video_id}")
            LOGGER(__name__).info(f"🎵 العنوان: {title[:30]}...")
            LOGGER(__name__).info(f"🎤 الفنان: {artist[:20]}...")
            
            # معالجة المدة
            duration = 0
            if isinstance(duration_text, str) and ':' in duration_text:
                try:
                    parts = duration_text.split(':')
                    if len(parts) == 2:
                        duration = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                except (ValueError, IndexError):
                    duration = 0
            
            if not video_id:
                return None
            
            self.method_performance['youtube_search']['avg_time'] = (
                self.method_performance['youtube_search']['avg_time'] * 0.7 + 
                (time.time() - start_time) * 0.3
            )
            
            return {
                "video_id": video_id,
                "title": title[:60],
                "artist": artist[:40] if artist else "Unknown Artist",
                "duration": duration,
                "thumb": thumb,
                "link": f"https://youtube.com/watch?v={video_id}",
                "source": "youtube_search"
            }
            
        except Exception as e:
            LOGGER(__name__).warning(f"فشل YouTube Search: {e}")
            try:
                self.monitor.log_error('youtube_search')
            except:
                pass
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
            cached_result = await self.search_in_smart_cache(query)
            if cached_result:
                LOGGER(__name__).info(f"⚡ كاش فوري: {query} ({time.time() - start_time:.3f}s)")
                # تحويل النتيجة إلى التنسيق المطلوب
                return {
                    'audio_path': cached_result.get('file_path'),
                    'title': cached_result.get('title', 'Unknown'),
                    'artist': cached_result.get('artist', 'Unknown'),
                    'duration': cached_result.get('duration', 0),
                    'source': 'smart_cache',
                    'cached': True
                }
            
            # خطوة 2: البحث عن معلومات الفيديو بالتوازي
            search_methods = []
            
            # إضافة طرق البحث بترتيب الأولوية
            
            # أولوية 1: YouTube Search (الأكثر موثوقية)
            try:
                if YoutubeSearch:
                    search_methods.append(self.youtube_search_simple(query))
                    LOGGER(__name__).info(f"🔍 إضافة YouTube Search للبحث")
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ فشل في إضافة YouTube Search: {e}")
            
            # أولوية 2: YouTube API (إذا كان متاحاً)
            if API_KEYS_CYCLE:
                search_methods.append(self.youtube_api_search(query))
                LOGGER(__name__).info(f"🔍 إضافة YouTube API للبحث")
            
            # أولوية 3: Invidious (كبديل)
            if INVIDIOUS_CYCLE:
                search_methods.append(self.invidious_search(query))
                LOGGER(__name__).info(f"🔍 إضافة Invidious للبحث")
            
            if not search_methods:
                LOGGER(__name__).error(f"❌ لا توجد طرق بحث متاحة!")
                return None
            
            LOGGER(__name__).info(f"🚀 بدء البحث بـ {len(search_methods)} طريقة")
            
            # تشغيل جميع عمليات البحث بالتوازي
            search_tasks = [asyncio.create_task(method) for method in search_methods]
            done, pending = await asyncio.wait(
                search_tasks,
                timeout=REQUEST_TIMEOUT * 1.5,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # إلغاء المهام المتبقية
            for task in pending:
                task.cancel()
            
            # أخذ أول نتيجة ناجحة
            video_info = None
            for task in done:
                try:
                    result = task.result()
                    if result:
                        video_info = result
                        LOGGER(__name__).info(f"✅ نجح البحث: {result.get('title', 'Unknown')} من {result.get('source', 'Unknown')}")
                        break
                except Exception as e:
                    LOGGER(__name__).warning(f"⚠️ فشلت إحدى طرق البحث: {e}")
            
            if not video_info:
                LOGGER(__name__).error(f"❌ فشل جميع طرق البحث لـ: {query}")
                return None
            
            # خطوة 3: تحميل الصوت
            LOGGER(__name__).info(f"🎵 بدء تحميل الصوت: {video_info.get('title', 'Unknown')}")
            audio_info = await self.download_with_ytdlp(video_info)
            if not audio_info:
                LOGGER(__name__).warning(f"⚠️ فشل التحميل الأساسي، جاري المحاولة الاحتياطية...")
                # محاولة نسخة احتياطية
                audio_info = await self.download_without_cookies(video_info)
                if not audio_info:
                    LOGGER(__name__).error(f"❌ فشل جميع طرق التحميل لـ: {video_info.get('title', 'Unknown')}")
                    return None
                else:
                    LOGGER(__name__).info(f"✅ نجح التحميل الاحتياطي: {audio_info.get('title', 'Unknown')}")
            else:
                LOGGER(__name__).info(f"✅ نجح التحميل الأساسي: {audio_info.get('title', 'Unknown')}")
            
            # خطوة 4: حفظ في التخزين الذكي (في الخلفية)
            if SMART_CACHE_CHANNEL:
                try:
                    # سيتم الحفظ في دالة send_audio_file
                    pass
                except Exception as cache_error:
                    LOGGER(__name__).warning(f"⚠️ خطأ في حفظ التخزين: {cache_error}")
            
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
            # self.monitor.log_error('hyper_download')
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
            
            # الحصول على ملفات الكوكيز المتاحة مع التدوير الذكي
            cookies_files = get_available_cookies()
            LOGGER(__name__).info(f"🍪 متاح: {len(cookies_files)} ملف كوكيز للتدوير")
            
            # إعداد محاولات التحميل مع الكوكيز المختلفة
            ydl_configs = []
            
            # إضافة محاولات مع كل ملف كوكيز مع التوزيع الديناميكي
            distribution = calculate_cookies_distribution(len(cookies_files))
            primary_count = distribution['primary']
            
            LOGGER(__name__).info(f"🍪 التوزيع الديناميكي: أساسي={primary_count}, ثانوي={distribution['secondary']}, متبقي={distribution['remaining']}")
            
            for i, cookie_file in enumerate(cookies_files[:primary_count], 1):
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
                    '_cookie_file': cookie_file,  # تتبع ملف الكوكيز
                    '_cookie_index': i  # رقم الكوكيز
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
            
            # جرب كل إعداد حتى ينجح أحدهم مع تتبع الكوكيز
            for i, ydl_opts in enumerate(ydl_configs, 1):
                cookie_file = ydl_opts.get('_cookie_file')
                
                try:
                    LOGGER(__name__).info(f"🔄 محاولة التحميل #{i}")
                    if cookie_file:
                        LOGGER(__name__).info(f"🍪 استخدام كوكيز: {os.path.basename(cookie_file)}")
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(
                            f"https://www.youtube.com/watch?v={video_id}",
                            download=True
                        )
                        
                        if info:
                            # البحث عن الملف المحمل
                            LOGGER(__name__).info(f"✅ تم التحميل بنجاح بالمحاولة #{i}: {info.get('title', title)}")
                            
                            # تتبع نجاح الكوكيز
                            if cookie_file:
                                track_cookie_usage(cookie_file, success=True)
                            
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
                    error_msg = str(e).lower()
                    LOGGER(__name__).warning(f"❌ فشلت المحاولة #{i}: {e}")
                    
                    # تتبع فشل الكوكيز
                    if cookie_file:
                        track_cookie_usage(cookie_file, success=False)
                    
                    # فحص أخطاء الحظر والكوكيز المنتهية الصلاحية
                    if cookie_file and any(keyword in error_msg for keyword in [
                        'blocked', 'forbidden', '403', 'unavailable', 'cookies', 'expired',
                        'sign in', 'login', 'authentication', 'token', 'session', 'captcha'
                    ]):
                        mark_cookie_as_blocked(cookie_file, f"خطأ: {str(e)[:50]}")
                        LOGGER(__name__).warning(f"🚫 تم حظر الكوكيز بسبب: {str(e)[:50]}")
                    
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
            # self.monitor.log_error('fallback_download')
        finally:
            self.active_tasks.discard(task_id)
            
        return None

# نظام تتبع حالة ملفات الكوكيز
COOKIES_STATUS = {}
BLOCKED_COOKIES = set()
COOKIES_USAGE_COUNT = {}
LAST_COOKIE_USED = None

# إحصائيات البحث المتوازي
PARALLEL_SEARCH_STATS = {
    'database_wins': 0,
    'smart_cache_wins': 0,
    'total_searches': 0,
    'avg_database_time': 0,
    'avg_smart_cache_time': 0,
    'database_times': [],
    'smart_cache_times': []
}

# نظام إدارة الحمولة العالية

# إعدادات الحمولة العالية (محسنة للأداء)
MAX_CONCURRENT_DOWNLOADS = 20          # حد معقول للتحميلات المتوازية
MAX_CONCURRENT_SEARCHES = 30           # حد معقول للبحث المتوازي
MAX_QUEUE_SIZE = float('inf')          # لا حد أقصى للطابور
RATE_LIMIT_WINDOW = 60                  # نافزة زمنية بالثواني
MAX_REQUESTS_PER_WINDOW = 1000          # حد مرن للطلبات (مضاعف)

# أدوات إدارة الموارد (بدون حدود)
# download_semaphore = None  # إزالة التحديد
# search_semaphore = None    # إزالة التحديد
thread_pool = ThreadPoolExecutor(max_workers=100)  # زيادة عدد الخيوط

# تتبع معدل الطلبات (مرن)
request_times = defaultdict(lambda: deque(maxlen=MAX_REQUESTS_PER_WINDOW))
active_downloads = {}
# download_queue = asyncio.Queue()  # طابور بلا حدود (لن نحتاجه)

# إحصائيات الأداء
PERFORMANCE_STATS = {
    'total_requests': 0,
    'successful_downloads': 0,
    'failed_downloads': 0,
    'cache_hits': 0,
    'avg_response_time': 0,
    'peak_concurrent': 0,
    'current_concurrent': 0,
    'queue_size': 0,
    'rate_limited': 0
}

async def check_rate_limit(user_id: int) -> bool:
    """فحص معدل الطلبات للمستخدم (مرن)"""
    current_time = time.time()
    user_requests = request_times[user_id]
    
    # إزالة الطلبات القديمة
    while user_requests and current_time - user_requests[0] > RATE_LIMIT_WINDOW:
        user_requests.popleft()
    
    # فحص مرن - تحذير فقط عند تجاوز الحد المقترح
    if len(user_requests) >= MAX_REQUESTS_PER_WINDOW:
        PERFORMANCE_STATS['rate_limited'] += 1
        # تسجيل تحذير لكن السماح بالمتابعة
        LOGGER(__name__).warning(f"⚠️ المستخدم {user_id} تجاوز الحد المقترح: {len(user_requests)} طلب في {RATE_LIMIT_WINDOW}s")
        
        # السماح بالمتابعة للحمولة العالية
        # return False  # معطل - لا حدود صارمة
    
    # إضافة الطلب الحالي
    user_requests.append(current_time)
    return True  # السماح دائماً

async def update_performance_stats(success: bool, response_time: float, from_cache: bool = False):
    """تحديث إحصائيات الأداء"""
    PERFORMANCE_STATS['total_requests'] += 1
    
    if success:
        PERFORMANCE_STATS['successful_downloads'] += 1
    else:
        PERFORMANCE_STATS['failed_downloads'] += 1
    
    if from_cache:
        PERFORMANCE_STATS['cache_hits'] += 1
    
    # تحديث متوسط وقت الاستجابة
    current_avg = PERFORMANCE_STATS['avg_response_time']
    total_requests = PERFORMANCE_STATS['total_requests']
    PERFORMANCE_STATS['avg_response_time'] = ((current_avg * (total_requests - 1)) + response_time) / total_requests
    
    # تحديث الذروة
    current_concurrent = len(active_downloads)
    PERFORMANCE_STATS['current_concurrent'] = current_concurrent
    if current_concurrent > PERFORMANCE_STATS['peak_concurrent']:
        PERFORMANCE_STATS['peak_concurrent'] = current_concurrent
    
    PERFORMANCE_STATS['queue_size'] = 0  # لا يوجد طابور - معالجة فورية

def log_performance_stats():
    """تسجيل إحصائيات الأداء"""
    stats = PERFORMANCE_STATS
    success_rate = (stats['successful_downloads'] / max(stats['total_requests'], 1)) * 100
    cache_hit_rate = (stats['cache_hits'] / max(stats['total_requests'], 1)) * 100
    
    LOGGER(__name__).info(
        f"📊 الأداء: {stats['total_requests']} طلب | "
        f"نجاح: {success_rate:.1f}% | "
        f"كاش: {cache_hit_rate:.1f}% | "
        f"متوسط: {stats['avg_response_time']:.2f}s | "
        f"متوازي: {stats['current_concurrent']}/{stats['peak_concurrent']} | "
        f"طابور: {stats['queue_size']}"
    )

async def process_unlimited_download(event, user_id: int, start_time: float):
    """معالجة التحميل المتوازي الفوري"""
    task_id = f"{user_id}_{int(time.time() * 1000000)}"  # دقة عالية جداً
    
    try:
        # تسجيل بداية المهمة فوراً
        active_downloads[task_id] = {
            'user_id': user_id,
            'start_time': start_time,
            'task_id': task_id,
            'status': 'started'
        }
        
        LOGGER(__name__).info(f"🚀 بدء معالجة فورية للمستخدم {user_id} | المهمة: {task_id}")
        
        # تنفيذ المعالجة الكاملة في مهمة منفصلة
        await execute_parallel_download(event, user_id, start_time, task_id)
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في معالجة التحميل المتوازي: {e}")
        await update_performance_stats(False, time.time() - start_time)
    finally:
        # تنظيف المهمة
        if task_id in active_downloads:
            active_downloads[task_id]['status'] = 'completed'
            del active_downloads[task_id]

async def execute_parallel_download(event, user_id: int, start_time: float, task_id: str):
    """تنفيذ التحميل المتوازي الكامل"""
    try:
        # استخراج الاستعلام
        match = event.pattern_match
        if not match:
            await event.reply("❌ **خطأ في تحليل الطلب**")
            return
        
        query = match.group(2) if match.group(2) else ""
        if not query:
            await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
            await update_performance_stats(False, time.time() - start_time)
            return
        
        # تحديث حالة المهمة
        if task_id in active_downloads:
            active_downloads[task_id].update({
                'query': query,
                'status': 'processing'
            })
        
        LOGGER(__name__).info(f"🎵 معالجة متوازية: {query} | المستخدم: {user_id} | المهمة: {task_id}")
        
        # تنفيذ البحث والتحميل مباشرة
        await process_normal_download(event, query, user_id, start_time)
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في تنفيذ التحميل المتوازي: {e}")
        await event.reply("❌ **حدث خطأ في معالجة طلبك**")
        await update_performance_stats(False, time.time() - start_time)

async def process_normal_download(event, query: str, user_id: int, start_time: float):
    """معالجة التحميل العادي مع إدارة الموارد"""
    bot_client = event.client
    
    try:
        # التحقق من أن المرسل ليس بوت
        if event.sender.bot:
            return
        
        # استخراج الاستعلام إذا لم يكن متوفراً
        if not query:
            match = event.pattern_match
            if not match:
                return
            
            query = match.group(2) if match.group(2) else ""
            if not query:
                await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
                await update_performance_stats(False, time.time() - start_time)
                return
        
        # إرسال رسالة الحالة
        status_msg = await event.reply("🔍 **جاري البحث في التخزين الذكي...**")
        
        # البحث المتوازي بدون حدود
        parallel_result = await parallel_search_with_monitoring(query, bot_client)
        
        if parallel_result and parallel_result.get('success'):
            search_source = parallel_result.get('search_source', 'unknown')
            search_time = parallel_result.get('search_time', 0)
            
            # تحديث الإحصائيات
            await update_performance_stats(True, time.time() - start_time, from_cache=True)
            
            if search_source == 'database':
                await status_msg.edit(f"📤 **تم العثور في الكاش ({search_time:.2f}s) - جاري الإرسال...**")
                await send_cached_from_database(event, status_msg, parallel_result, bot_client)
                return
            elif search_source == 'smart_cache':
                await status_msg.edit(f"📤 **تم العثور في التخزين الذكي ({search_time:.2f}s) - جاري الإرسال...**")
                await send_cached_audio(event, status_msg, parallel_result, bot_client)
                return
        
        # إذا لم يجد في التخزين، ابدأ التحميل العادي
        await status_msg.edit("🔍 **لم يوجد في التخزين - جاري البحث في يوتيوب...**")
        
        # هنا يتم استدعاء باقي منطق التحميل العادي الموجود
        # (سيتم ربطه مع الكود الموجود)
        
        # تحديث الإحصائيات
        await update_performance_stats(True, time.time() - start_time)
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في المعالجة العادية: {e}")
        await update_performance_stats(False, time.time() - start_time)
        
        try:
            await status_msg.edit("❌ **حدث خطأ أثناء المعالجة**")
        except:
            pass

def get_available_cookies():
    """الحصول على قائمة ملفات الكوكيز المتاحة مع تدوير ذكي"""
    try:
        import glob
        import os
        cookies_pattern = "cookies/cookies*.txt"
        all_cookies_files = glob.glob(cookies_pattern)
        
        # إزالة الملفات المحظورة
        available_cookies = []
        for cookie_file in all_cookies_files:
            if cookie_file not in BLOCKED_COOKIES:
                available_cookies.append(cookie_file)
        
        if not available_cookies:
            LOGGER(__name__).warning("⚠️ جميع ملفات الكوكيز محظورة! جاري إعادة تعيين...")
            BLOCKED_COOKIES.clear()
            available_cookies = all_cookies_files
        
        # ترتيب ذكي: الأقل استخداماً أولاً
        available_cookies.sort(key=lambda x: (
            COOKIES_USAGE_COUNT.get(x, 0),  # عدد مرات الاستخدام
            os.path.getmtime(x)  # تاريخ التعديل
        ))
        
        LOGGER(__name__).info(f"🍪 متاح: {len(available_cookies)} | محظور: {len(BLOCKED_COOKIES)} ملف كوكيز")
        return available_cookies
    except Exception as e:
        LOGGER(__name__).warning(f"❌ خطأ في قراءة ملفات الكوكيز: {e}")
        return []

def mark_cookie_as_blocked(cookie_file: str, reason: str = "حظر"):
    """تمييز ملف كوكيز كمحظور وحذفه"""
    try:
        BLOCKED_COOKIES.add(cookie_file)
        LOGGER(__name__).warning(f"🚫 تم حظر الكوكيز: {os.path.basename(cookie_file)} - {reason}")
        
        # نسخ احتياطي قبل الحذف
        backup_name = f"{cookie_file}.blocked_{int(time.time())}"
        if os.path.exists(cookie_file):
            os.rename(cookie_file, backup_name)
            LOGGER(__name__).info(f"💾 تم نسخ الكوكيز المحظور إلى: {os.path.basename(backup_name)}")
        
        # تنظيف الإحصائيات
        if cookie_file in COOKIES_USAGE_COUNT:
            del COOKIES_USAGE_COUNT[cookie_file]
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في حظر الكوكيز: {e}")

def track_cookie_usage(cookie_file: str, success: bool = True):
    """تتبع استخدام ملف الكوكيز"""
    global LAST_COOKIE_USED
    
    COOKIES_USAGE_COUNT[cookie_file] = COOKIES_USAGE_COUNT.get(cookie_file, 0) + 1
    LAST_COOKIE_USED = cookie_file
    
    status = "✅" if success else "❌"
    usage_count = COOKIES_USAGE_COUNT[cookie_file]
    
    LOGGER(__name__).info(f"{status} كوكيز: {os.path.basename(cookie_file)} (استخدام #{usage_count})")

def get_next_cookie_with_rotation():
    """الحصول على ملف الكوكيز التالي مع تدوير ذكي"""
    available_cookies = get_available_cookies()
    
    if not available_cookies:
        return None
    
    # تجنب استخدام نفس الكوكيز المستخدم مؤخراً
    if LAST_COOKIE_USED and len(available_cookies) > 1:
        try:
            available_cookies.remove(LAST_COOKIE_USED)
        except ValueError:
            pass
    
    # اختيار الكوكيز الأقل استخداماً
    next_cookie = available_cookies[0]
    LOGGER(__name__).info(f"🔄 تدوير إلى كوكيز: {os.path.basename(next_cookie)}")
    
    return next_cookie

def cleanup_blocked_cookies():
    """تنظيف دوري للكوكيز المحظورة"""
    try:
        import glob
        # إذا تم حظر أكثر من 70% من الكوكيز، اعد تعيين النظام
        total_cookies = len(glob.glob("cookies/cookies*.txt"))
        blocked_count = len(BLOCKED_COOKIES)
        
        if total_cookies > 0 and (blocked_count / total_cookies) > 0.7:
            LOGGER(__name__).warning(f"⚠️ تم حظر {blocked_count}/{total_cookies} كوكيز - إعادة تعيين النظام")
            BLOCKED_COOKIES.clear()
            COOKIES_USAGE_COUNT.clear()
            
        # حذف ملفات الكوكيز الاحتياطية القديمة (أكثر من 24 ساعة)
        import time
        current_time = time.time()
        
        for backup_file in glob.glob("cookies/*.blocked_*"):
            try:
                file_time = os.path.getmtime(backup_file)
                if current_time - file_time > 86400:  # 24 ساعة
                    os.remove(backup_file)
                    LOGGER(__name__).info(f"🗑️ تم حذف النسخة الاحتياطية القديمة: {os.path.basename(backup_file)}")
            except Exception as e:
                LOGGER(__name__).warning(f"❌ خطأ في حذف النسخة الاحتياطية: {e}")
                
        LOGGER(__name__).info(f"🧹 تنظيف الكوكيز: متاح={total_cookies-blocked_count} | محظور={blocked_count}")
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في تنظيف الكوكيز: {e}")

def calculate_cookies_distribution(total_count: int) -> Dict[str, int]:
    """حساب توزيع الكوكيز بشكل ديناميكي"""
    if total_count == 0:
        return {'primary': 0, 'secondary': 0, 'remaining': 0}
    
    # توزيع ذكي حسب العدد الإجمالي
    if total_count <= 5:
        # عدد قليل: استخدم الكل في المرحلة الأساسية
        return {'primary': total_count, 'secondary': 0, 'remaining': 0}
    
    elif total_count <= 10:
        # عدد متوسط: قسم بين أساسي وثانوي
        primary = total_count // 2
        secondary = total_count - primary
        return {'primary': primary, 'secondary': secondary, 'remaining': 0}
    
    elif total_count <= 20:
        # عدد كبير: توزيع متوازن
        primary = max(4, total_count // 3)
        secondary = max(3, total_count // 4)
        remaining = total_count - primary - secondary
        return {'primary': primary, 'secondary': secondary, 'remaining': remaining}
    
    else:
        # عدد كبير جداً: توزيع محدود لتجنب الإفراط
        primary = min(8, max(5, total_count // 4))
        secondary = min(6, max(4, total_count // 5))
        remaining = min(10, total_count - primary - secondary)
        return {'primary': primary, 'secondary': secondary, 'remaining': remaining}

def get_cookies_statistics():
    """إحصائيات استخدام الكوكيز مع التوزيع الديناميكي"""
    try:
        import glob
        total_cookies = len(glob.glob("cookies/cookies*.txt"))
        available_cookies = len(get_available_cookies())
        blocked_cookies = len(BLOCKED_COOKIES)
        
        # حساب التوزيع الديناميكي
        distribution = calculate_cookies_distribution(available_cookies)
        
        # أكثر الكوكيز استخداماً
        most_used = max(COOKIES_USAGE_COUNT.items(), key=lambda x: x[1]) if COOKIES_USAGE_COUNT else ("لا يوجد", 0)
        
        stats = {
            'total': total_cookies,
            'available': available_cookies, 
            'blocked': blocked_cookies,
            'distribution': distribution,
            'most_used_file': os.path.basename(most_used[0]) if most_used[0] != "لا يوجد" else "لا يوجد",
            'most_used_count': most_used[1],
            'usage_distribution': dict(COOKIES_USAGE_COUNT)
        }
        
        return stats
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إحصائيات الكوكيز: {e}")
        return {}

async def parallel_search_with_monitoring(query: str, bot_client) -> Optional[Dict]:
    """البحث المتوازي مع مراقبة الأداء"""
    start_time = time.time()
    
    try:
        LOGGER(__name__).info(f"🚀 بدء البحث المتوازي: {query}")
        
        # إنشاء مهام متوازية مع تتبع الوقت
        db_task = asyncio.create_task(search_in_database_cache(query))
        cache_task = asyncio.create_task(search_in_telegram_cache(query, bot_client))
        
        # تسجيل بدء المهام
        db_start = time.time()
        cache_start = time.time()
        
        # انتظار أول نتيجة ناجحة
        done, pending = await asyncio.wait(
            [db_task, cache_task], 
            return_when=asyncio.FIRST_COMPLETED,
            timeout=10  # مهلة زمنية 10 ثوان
        )
        
        # فحص النتائج
        for task in done:
            try:
                result = await task
                if result and result.get('success'):
                    elapsed = time.time() - start_time
                    
                    # تحديث الإحصائيات
                    PARALLEL_SEARCH_STATS['total_searches'] += 1
                    
                    if task == db_task:
                        LOGGER(__name__).info(f"🏆 قاعدة البيانات فازت! ({elapsed:.2f}s)")
                        result['search_source'] = 'database'
                        result['search_time'] = elapsed
                        
                        # تحديث إحصائيات قاعدة البيانات
                        PARALLEL_SEARCH_STATS['database_wins'] += 1
                        PARALLEL_SEARCH_STATS['database_times'].append(elapsed)
                        if len(PARALLEL_SEARCH_STATS['database_times']) > 100:
                            PARALLEL_SEARCH_STATS['database_times'].pop(0)
                        PARALLEL_SEARCH_STATS['avg_database_time'] = sum(PARALLEL_SEARCH_STATS['database_times']) / len(PARALLEL_SEARCH_STATS['database_times'])
                        
                    elif task == cache_task:
                        LOGGER(__name__).info(f"🏆 التخزين الذكي فاز! ({elapsed:.2f}s)")
                        result['search_source'] = 'smart_cache'
                        result['search_time'] = elapsed
                        
                        # تحديث إحصائيات التخزين الذكي
                        PARALLEL_SEARCH_STATS['smart_cache_wins'] += 1
                        PARALLEL_SEARCH_STATS['smart_cache_times'].append(elapsed)
                        if len(PARALLEL_SEARCH_STATS['smart_cache_times']) > 100:
                            PARALLEL_SEARCH_STATS['smart_cache_times'].pop(0)
                        PARALLEL_SEARCH_STATS['avg_smart_cache_time'] = sum(PARALLEL_SEARCH_STATS['smart_cache_times']) / len(PARALLEL_SEARCH_STATS['smart_cache_times'])
                    
                    # إلغاء المهام المتبقية
                    for pending_task in pending:
                        pending_task.cancel()
                    
                    return result
                    
            except Exception as e:
                LOGGER(__name__).warning(f"❌ خطأ في مهمة البحث: {e}")
        
        # إذا لم تنجح المهام المكتملة، انتظر الباقي
        if pending:
            LOGGER(__name__).info("⏳ انتظار المهام المتبقية...")
            try:
                remaining_results = await asyncio.gather(*pending, return_exceptions=True)
                
                for i, result in enumerate(remaining_results):
                    if isinstance(result, Exception):
                        continue
                        
                    if result and result.get('success'):
                        elapsed = time.time() - start_time
                        remaining_tasks = list(pending)
                        
                        if remaining_tasks[i] == db_task:
                            LOGGER(__name__).info(f"✅ قاعدة البيانات نجحت (متأخرة: {elapsed:.2f}s)")
                            result['search_source'] = 'database'
                        elif remaining_tasks[i] == cache_task:
                            LOGGER(__name__).info(f"✅ التخزين الذكي نجح (متأخر: {elapsed:.2f}s)")
                            result['search_source'] = 'smart_cache'
                        
                        result['search_time'] = elapsed
                        return result
                        
            except asyncio.TimeoutError:
                LOGGER(__name__).warning("⏰ انتهت مهلة البحث المتوازي")
        
        total_time = time.time() - start_time
        LOGGER(__name__).info(f"❌ فشل البحث المتوازي ({total_time:.2f}s)")
        return None
        
    except Exception as e:
        total_time = time.time() - start_time
        LOGGER(__name__).error(f"❌ خطأ في البحث المتوازي ({total_time:.2f}s): {e}")
        return None

# === نظام البحث في قاعدة البيانات الذكية ===

async def search_in_database_cache(query: str) -> Optional[Dict]:
    """البحث في قاعدة البيانات الذكية (الكاش)"""
    try:
        # تنظيف النص للبحث
        normalized_query = normalize_search_text(query)
        search_keywords = normalized_query.split()
        
        LOGGER(__name__).info(f"🗄️ البحث في قاعدة البيانات: '{normalized_query}' (كلمات: {search_keywords})")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # البحث الذكي المحسن مع معالجة الاختلافات في الكتابة العربية
        search_conditions = []
        search_params = []
        
        # إضافة البحث الدقيق أولاً
        search_conditions.append("(title_normalized LIKE ? OR artist_normalized LIKE ?)")
        search_params.extend([f"%{normalized_query}%", f"%{normalized_query}%"])
        
        # معالجة الاختلافات الشائعة في الكتابة العربية
        arabic_variants = {
            'وحشتني': ['وحشتني', 'وحشتيني', 'وحشني', 'وحشتنى'],
            'احبك': ['احبك', 'أحبك', 'احبّك', 'أحبّك'],
            'حبيبي': ['حبيبي', 'حبيبى'],
            'عليك': ['عليك', 'عليكي'],
            'انت': ['انت', 'أنت', 'إنت']
        }
        
        # البحث بالمتغيرات العربية
        for original_word in search_keywords:
            if len(original_word) > 2:
                variants = arabic_variants.get(original_word, [original_word])
                for variant in variants:
                    search_conditions.append("(title_normalized LIKE ? OR artist_normalized LIKE ? OR keywords_vector LIKE ?)")
                    search_params.extend([f"%{variant}%", f"%{variant}%", f"%{variant}%"])
        
        # البحث العام بالكلمات المفردة (احتياطي)
        for keyword in search_keywords:
            if len(keyword) > 2:
                search_conditions.append("(title_normalized LIKE ? OR artist_normalized LIKE ? OR keywords_vector LIKE ?)")
                search_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        
        # استعلام البحث مع ترتيب حسب الشعبية وآخر وصول
        query_sql = f"""
        SELECT message_id, file_id, file_unique_id, original_title, original_artist, 
               duration, file_size, access_count, last_accessed, popularity_rank,
               title_normalized, artist_normalized
        FROM channel_index 
        WHERE ({' OR '.join(search_conditions)})
        ORDER BY popularity_rank DESC, access_count DESC, last_accessed DESC
        LIMIT 5
        """
        
        cursor.execute(query_sql, search_params)
        results = cursor.fetchall()
        
        LOGGER(__name__).info(f"🔍 تم العثور على {len(results)} نتيجة في قاعدة البيانات")
        
        if results:
            # اختيار أفضل نتيجة
            best_result = results[0]
            
            # تحديث إحصائيات الوصول
            cursor.execute("""
                UPDATE channel_index 
                SET access_count = access_count + 1, 
                    last_accessed = CURRENT_TIMESTAMP,
                    popularity_rank = popularity_rank + 0.1
                WHERE message_id = ?
            """, (best_result[0],))
            
            conn.commit()
            conn.close()
            
            # حساب نسبة التطابق
            title_words = set(best_result[10].split())  # title_normalized
            artist_words = set(best_result[11].split())  # artist_normalized
            query_words = set(search_keywords)
            
            all_content_words = title_words | artist_words
            match_ratio = len(query_words & all_content_words) / len(query_words) if query_words else 0
            
            # التحقق من الحد الأدنى للتطابق (80% على الأقل)
            MIN_MATCH_RATIO = 0.8
            if match_ratio < MIN_MATCH_RATIO:
                LOGGER(__name__).info(f"❌ نسبة التطابق منخفضة جداً: {match_ratio:.1%} (الحد الأدنى: {MIN_MATCH_RATIO:.1%})")
                conn.close()
                return None
            
            LOGGER(__name__).info(f"✅ تم العثور على مطابقة قوية في قاعدة البيانات: {match_ratio:.1%}")
            
            return {
                'success': True,
                'cached': True,
                'from_database': True,
                'message_id': best_result[0],
                'file_id': best_result[1],
                'file_unique_id': best_result[2],
                'title': best_result[3],  # original_title
                'uploader': best_result[4],  # original_artist
                'duration': best_result[5],
                'file_size': best_result[6],
                'access_count': best_result[7] + 1,
                'match_ratio': match_ratio
            }
        
        conn.close()
        LOGGER(__name__).info("❌ لم يتم العثور على مطابقة في قاعدة البيانات")
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في البحث بقاعدة البيانات: {e}")
        return None

async def send_cached_from_database(event, status_msg, db_result: Dict, bot_client):
    """إرسال الملف من قاعدة البيانات باستخدام file_id"""
    try:
        import config
        
        LOGGER(__name__).info(f"📤 محاولة إرسال من قاعدة البيانات: {db_result.get('title', 'Unknown')}")
        await status_msg.edit("📤 **إرسال من الكاش المحلي...**")
        
        # تحضير التسمية التوضيحية
        duration = db_result.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
        
        user_caption = f"✦ @{config.BOT_USERNAME}"
        
        # محاولة تحميل الصورة المصغرة إذا كانت متاحة
        thumb_path = None
        try:
            title = db_result.get('title', 'Unknown')
            # البحث عن الصورة المصغرة في قناة التخزين
            if 'message_id' in db_result and bot_client:
                try:
                    if hasattr(config, 'CACHE_CHANNEL_ID') and config.CACHE_CHANNEL_ID:
                        # الحصول على الرسالة من قناة التخزين للحصول على الصورة المصغرة
                        channel_msg = await bot_client.get_messages(config.CACHE_CHANNEL_ID, ids=db_result['message_id'])
                        if channel_msg and channel_msg.media and hasattr(channel_msg.media, 'document'):
                            # استخراج الصورة المصغرة من الملف
                            if hasattr(channel_msg.media.document, 'thumbs') and channel_msg.media.document.thumbs:
                                thumb_path = channel_msg.media.document.thumbs[0]
                                LOGGER(__name__).info(f"📸 تم العثور على الصورة المصغرة من قناة التخزين")
                except Exception as thumb_error:
                    LOGGER(__name__).warning(f"⚠️ خطأ في الحصول على الصورة المصغرة: {thumb_error}")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في معالجة الصورة المصغرة: {e}")
        
        LOGGER(__name__).info(f"📋 معلومات الإرسال: file_id={db_result['file_id'][:20]}..., duration={duration}")
        
        # إرسال الملف كرد على رسالة المستخدم
        sent_message = await event.reply(
            user_caption,
            file=db_result['file_id'],
            thumb=thumb_path,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=db_result.get('title', 'Unknown')[:60],
                    performer=db_result.get('uploader', 'Unknown')[:40]
                )
            ]
        )
        
        await status_msg.delete()
        LOGGER(__name__).info(f"✅ تم إرسال الملف من قاعدة البيانات كرد بنجاح: {sent_message.id}")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الملف من قاعدة البيانات: {e}")
        # إزالة الرسالة المزعجة - الانتقال مباشرة للتحميل
        return False

async def send_cached_from_telegram(event, status_msg, cache_result: Dict, bot_client):
    """إرسال الملف من التخزين الذكي (قناة التخزين)"""
    try:
        import config
        
        LOGGER(__name__).info(f"📤 محاولة إرسال من التخزين الذكي: {cache_result.get('title', 'Unknown')}")
        await status_msg.edit("📤 **إرسال من التخزين الذكي...**")
        
        # تحضير التسمية التوضيحية
        duration = cache_result.get('duration', 0)
        user_caption = f"✦ @{config.BOT_USERNAME}"
        
        # محاولة الحصول على الصورة المصغرة من قناة التخزين
        thumb_path = None
        try:
            if 'message_id' in cache_result and bot_client:
                try:
                    if hasattr(config, 'CACHE_CHANNEL_ID') and config.CACHE_CHANNEL_ID:
                        # الحصول على الرسالة من قناة التخزين للحصول على الصورة المصغرة
                        channel_msg = await bot_client.get_messages(config.CACHE_CHANNEL_ID, ids=cache_result['message_id'])
                        if channel_msg and channel_msg.media and hasattr(channel_msg.media, 'document'):
                            # استخراج الصورة المصغرة من الملف
                            if hasattr(channel_msg.media.document, 'thumbs') and channel_msg.media.document.thumbs:
                                thumb_path = channel_msg.media.document.thumbs[0]
                                LOGGER(__name__).info(f"📸 تم العثور على الصورة المصغرة من قناة التخزين")
                except Exception as thumb_error:
                    LOGGER(__name__).warning(f"⚠️ خطأ في الحصول على الصورة المصغرة: {thumb_error}")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في معالجة الصورة المصغرة: {e}")
        
        LOGGER(__name__).info(f"📋 معلومات الإرسال: file_id={cache_result['file_id'][:20]}..., duration={duration}")
        
        # إرسال الملف كرد على رسالة المستخدم
        sent_message = await event.reply(
            user_caption,
            file=cache_result['file_id'],
            thumb=thumb_path,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=cache_result.get('title', 'Unknown')[:60],
                    performer=cache_result.get('uploader', 'Unknown')[:40]
                )
            ]
        )
        
        await status_msg.delete()
        LOGGER(__name__).info(f"✅ تم إرسال الملف من التخزين الذكي كرد بنجاح: {sent_message.id}")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الملف من التخزين الذكي: {e}")
        # إزالة الرسالة المزعجة - الانتقال مباشرة للتحميل
        return False

async def save_to_database_cache(file_id: str, file_unique_id: str, message_id: int, result: Dict, query: str) -> bool:
    """حفظ معلومات الملف في قاعدة البيانات الذكية"""
    try:
        # تنظيف وتطبيع البيانات
        title = result.get('title', 'Unknown')
        artist = result.get('uploader', 'Unknown')
        duration = result.get('duration', 0)
        file_size = result.get('file_size', 0)
        
        title_normalized = normalize_search_text(title)
        artist_normalized = normalize_search_text(artist)
        
        # إنشاء vector الكلمات المفتاحية
        keywords_vector = f"{title_normalized} {artist_normalized} {normalize_search_text(query)}"
        
        # إنشاء هاش البحث
        search_hash = hashlib.md5((title_normalized + artist_normalized).encode()).hexdigest()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # إدخال البيانات (أو تحديثها إذا كانت موجودة)
        cursor.execute("""
            INSERT OR REPLACE INTO channel_index 
            (message_id, file_id, file_unique_id, search_hash, title_normalized, 
             artist_normalized, keywords_vector, original_title, original_artist, 
             duration, file_size, access_count, popularity_rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1.0)
        """, (
            message_id, file_id, file_unique_id, search_hash,
            title_normalized, artist_normalized, keywords_vector,
            title, artist, duration, file_size
        ))
        
        conn.commit()
        conn.close()
        
        LOGGER(__name__).info(f"✅ تم حفظ الملف في قاعدة البيانات: {title[:30]}")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في حفظ قاعدة البيانات: {e}")
        return False

# === نظام التخزين الذكي في قناة التيليجرام ===

async def search_in_telegram_cache(query: str, bot_client) -> Optional[Dict]:
    """البحث الذكي الخارق في قناة التخزين مع فهرسة متقدمة"""
    try:
        import config
        
        if not hasattr(config, 'CACHE_CHANNEL_ID') or not config.CACHE_CHANNEL_ID:
            LOGGER(__name__).warning("❌ قناة التخزين غير محددة")
            return None
        
        cache_channel = config.CACHE_CHANNEL_ID
        LOGGER(__name__).info(f"🔍 البحث الذكي الخارق في التخزين: {cache_channel}")
        
        # تنظيف النص للبحث
        normalized_query = normalize_search_text(query)
        search_keywords = normalized_query.split()
        
        # الخطوة 1: البحث السريع في قاعدة البيانات أولاً (أسرع)
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # بحث متقدم بالكلمات المفتاحية مع معالجة الاختلافات العربية
            search_conditions = []
            search_params = []
            
            # إضافة البحث الدقيق أولاً
            search_conditions.append("(title_normalized LIKE ? OR artist_normalized LIKE ?)")
            search_params.extend([f"%{normalized_query}%", f"%{normalized_query}%"])
            
            # معالجة الاختلافات الشائعة في الكتابة العربية
            arabic_variants = {
                'وحشتني': ['وحشتني', 'وحشتيني', 'وحشني', 'وحشتنى'],
                'احبك': ['احبك', 'أحبك', 'احبّك', 'أحبّك'],
                'حبيبي': ['حبيبي', 'حبيبى'],
                'عليك': ['عليك', 'عليكي'],
                'انت': ['انت', 'أنت', 'إنت']
            }
            
            # البحث بالمتغيرات العربية
            for original_word in search_keywords:
                if len(original_word) > 2:
                    variants = arabic_variants.get(original_word, [original_word])
                    for variant in variants:
                        search_conditions.append("(title_normalized LIKE ? OR artist_normalized LIKE ? OR keywords_vector LIKE ?)")
                        search_params.extend([f"%{variant}%", f"%{variant}%", f"%{variant}%"])
            
            # استعلام محسن مع ترتيب ذكي
            query_sql = f"""
            SELECT message_id, file_id, file_unique_id, original_title, original_artist, 
                   duration, file_size, access_count, last_accessed, popularity_rank,
                   title_normalized, artist_normalized, keywords_vector
            FROM channel_index 
            WHERE ({' OR '.join(search_conditions)})
            ORDER BY 
                -- أولوية للمطابقة الكاملة
                CASE WHEN title_normalized LIKE '%{normalized_query}%' THEN 1 ELSE 2 END,
                -- ثم حسب الشعبية
                popularity_rank DESC, 
                access_count DESC, 
                last_accessed DESC
            LIMIT 10
            """
            
            cursor.execute(query_sql, search_params)
            db_results = cursor.fetchall()
            
            if db_results:
                # حساب نسبة التطابق لكل نتيجة
                best_match = None
                best_score = 0
                
                for result in db_results:
                    # حساب درجة التطابق المتقدمة
                    title_words = set(result[10].split())  # title_normalized
                    artist_words = set(result[11].split())  # artist_normalized
                    keywords_words = set(result[12].split())  # keywords_vector
                    query_words = set(search_keywords)
                    
                    # حساب التطابق المتعدد المستويات
                    title_match = len(query_words & title_words) / len(query_words) if query_words else 0
                    artist_match = len(query_words & artist_words) / len(query_words) if query_words else 0
                    keywords_match = len(query_words & keywords_words) / len(query_words) if query_words else 0
                    
                    # درجة مركبة مع أوزان
                    composite_score = (
                        title_match * 0.5 +      # وزن العنوان 50%
                        artist_match * 0.3 +     # وزن الفنان 30%
                        keywords_match * 0.2     # وزن الكلمات المفتاحية 20%
                    )
                    
                    # إضافة بونص للشعبية
                    popularity_bonus = min(result[9] / 10, 0.1)  # أقصى بونص 10%
                    composite_score += popularity_bonus
                    
                    if composite_score > best_score and composite_score > 0.8:  # حد أدنى 80%
                        best_score = composite_score
                        best_match = result
                
                if best_match:
                    # تحديث إحصائيات الوصول
                    cursor.execute("""
                        UPDATE channel_index 
                        SET access_count = access_count + 1, 
                            last_accessed = CURRENT_TIMESTAMP,
                            popularity_rank = popularity_rank + 0.1
                        WHERE message_id = ?
                    """, (best_match[0],))
                    conn.commit()
                    
                    LOGGER(__name__).info(f"✅ مطابقة قوية في التخزين الذكي: {best_score:.1%}")
                    
                    conn.close()
                    return {
                        'success': True,
                        'cached': True,
                        'from_database': True,
                        'message_id': best_match[0],
                        'file_id': best_match[1],
                        'file_unique_id': best_match[2],
                        'title': best_match[3],
                        'uploader': best_match[4],
                        'duration': best_match[5],
                        'file_size': best_match[6],
                        'access_count': best_match[7] + 1,
                        'match_ratio': best_score
                    }
            
            conn.close()
            
            # إذا لم نجد مطابقة قوية
            if not best_match:
                LOGGER(__name__).info("❌ لم يتم العثور على مطابقة قوية في التخزين الذكي (الحد الأدنى: 80%)")
            
        except Exception as db_error:
            LOGGER(__name__).warning(f"⚠️ خطأ في البحث بقاعدة البيانات: {db_error}")
        
        # الخطوة 2: البحث المتقدم في رسائل القناة معطل (قيود API للبوتات)
        LOGGER(__name__).info("⚠️ البحث في التخزين الذكي معطل مؤقتاً (قيود API للبوتات)")
        return None  # تعطيل البحث في التخزين الذكي
        
        # زيادة عدد الرسائل المفحوصة إلى 500 رسالة مع تحسين الأداء
        search_limit = 500
        batch_size = 50  # معالجة على دفعات لتحسين الأداء
        
        best_matches = []
        processed_count = 0
        
        # معالجة الرسائل على دفعات
        async for message in bot_client.iter_messages(cache_channel, limit=search_limit):
            if not (message.text and message.file):
                continue
                
            processed_count += 1
            
            # تحليل النص المتقدم
            message_text = message.text.lower()
            
            # استخراج المعلومات من النص
            title = extract_title_from_cache_text(message.text)
            uploader = extract_uploader_from_cache_text(message.text)
            duration = extract_duration_from_cache_text(message.text)
            
            # تطبيع المعلومات المستخرجة
            title_normalized = normalize_search_text(title)
            uploader_normalized = normalize_search_text(uploader)
            
            # حساب التطابق المتقدم
            title_words = set(title_normalized.split())
            uploader_words = set(uploader_normalized.split())
            message_words = set(normalize_search_text(message_text).split())
            query_words = set(search_keywords)
            
            # حساب درجات التطابق
            title_match = len(query_words & title_words) / len(query_words) if query_words else 0
            uploader_match = len(query_words & uploader_words) / len(query_words) if query_words else 0
            message_match = len(query_words & message_words) / len(query_words) if query_words else 0
            
            # درجة مركبة محسنة
            composite_score = (
                title_match * 0.4 +        # وزن العنوان 40%
                uploader_match * 0.3 +     # وزن الفنان 30%
                message_match * 0.3        # وزن النص الكامل 30%
            )
            
            # إضافة بونص للرسائل الحديثة
            age_bonus = min((search_limit - processed_count) / search_limit * 0.1, 0.1)
            composite_score += age_bonus
            
            if composite_score > 0.5:  # حد أدنى 50% للتطابق
                best_matches.append({
                    'score': composite_score,
                    'message': message,
                    'title': title,
                    'uploader': uploader,
                    'duration': duration,
                    'message_id': message.id,
                    'file_id': message.file.id
                })
            
            # معالجة على دفعات لتحسين الأداء
            if processed_count % batch_size == 0:
                # ترتيب أفضل النتائج حتى الآن
                best_matches = sorted(best_matches, key=lambda x: x['score'], reverse=True)[:5]
                LOGGER(__name__).info(f"🔄 تم معالجة {processed_count} رسالة، أفضل تطابق: {best_matches[0]['score']:.1%}" if best_matches else f"🔄 تم معالجة {processed_count} رسالة")
        
        # اختيار أفضل نتيجة
        if best_matches:
            best_matches = sorted(best_matches, key=lambda x: x['score'], reverse=True)
            best_result = best_matches[0]
            
            LOGGER(__name__).info(f"✅ أفضل مطابقة في القناة: {best_result['score']:.1%} من {processed_count} رسالة")
            
            # حفظ النتيجة في قاعدة البيانات للمرات القادمة
            try:
                file_info = {
                    'title': best_result['title'],
                    'uploader': best_result['uploader'],
                    'duration': best_result['duration'],
                    'file_size': best_result['message'].file.size if best_result['message'].file.size else 0
                }
                
                await save_to_database_cache(
                    best_result['file_id'],
                    best_result['message'].file.unique_id,
                    best_result['message_id'],
                    file_info,
                    query
                )
                LOGGER(__name__).info("💾 تم حفظ النتيجة في قاعدة البيانات للبحث السريع مستقبلاً")
                
            except Exception as save_error:
                LOGGER(__name__).warning(f"⚠️ خطأ في حفظ النتيجة: {save_error}")
            
            return {
                'success': True,
                'cached': True,
                'message_id': best_result['message_id'],
                'file_id': best_result['file_id'],
                'title': best_result['title'],
                'duration': best_result['duration'],
                'uploader': best_result['uploader'],
                'match_ratio': best_result['score'],
                'original_message': best_result['message'],
                'processed_messages': processed_count
            }
        
        LOGGER(__name__).info(f"❌ لم يتم العثور على مطابقة مناسبة من {processed_count} رسالة")
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في البحث الذكي بالتخزين: {e}")
        return None

# تم دمج هذه الدالة مع normalize_arabic_text
normalize_search_text = normalize_arabic_text  # توحيد الدوال

def extract_title_from_cache_text(text: str) -> str:
    """استخراج العنوان من نص التخزين"""
    try:
        import re
        
        # البحث عن العنوان بعد 🎵
        title_match = re.search(r'🎵\s*\*\*(.+?)\*\*', text)
        if title_match:
            return title_match.group(1).strip()
        
        # البحث عن العنوان بعد "العنوان:"
        title_match = re.search(r'العنوان:\s*(.+?)(?:\n|$)', text)
        if title_match:
            return title_match.group(1).strip()
        
        return "Unknown Title"
    except:
        return "Unknown Title"

def extract_duration_from_cache_text(text: str) -> int:
    """استخراج المدة من نص التخزين"""
    try:
        import re
        
        # البحث عن المدة بصيغة mm:ss
        duration_match = re.search(r'⏱️\s*\*\*(\d+):(\d+)\*\*', text)
        if duration_match:
            minutes = int(duration_match.group(1))
            seconds = int(duration_match.group(2))
            return minutes * 60 + seconds
        
        # البحث عن المدة بالثواني
        duration_match = re.search(r'المدة:\s*(\d+)', text)
        if duration_match:
            return int(duration_match.group(1))
        
        return 0
    except:
        return 0

def extract_uploader_from_cache_text(text: str) -> str:
    """استخراج اسم الرافع من نص التخزين"""
    try:
        import re
        
        # البحث عن الفنان بعد 🎤
        uploader_match = re.search(r'🎤\s*\*\*(.+?)\*\*', text)
        if uploader_match:
            return uploader_match.group(1).strip()
        
        # البحث عن الفنان بعد "الفنان:"
        uploader_match = re.search(r'الفنان:\s*(.+?)(?:\n|$)', text)
        if uploader_match:
            return uploader_match.group(1).strip()
        
        return "Unknown Artist"
    except:
        return "Unknown Artist"

async def save_to_smart_cache(bot_client, file_path: str, result: Dict, query: str, thumb_path: str = None) -> bool:
    """حفظ الملف في قناة التخزين الذكي مع فهرسة متقدمة وتفصيل شامل"""
    try:
        import config
        import os
        from pathlib import Path
        
        if not hasattr(config, 'CACHE_CHANNEL_ID') or not config.CACHE_CHANNEL_ID:
            LOGGER(__name__).warning("❌ قناة التخزين غير محددة - تخطي التخزين")
            return False
        
        cache_channel = config.CACHE_CHANNEL_ID
        
        # تحضير البيانات المفصلة
        title = result.get('title', 'Unknown')
        uploader = result.get('uploader', 'Unknown')
        duration = result.get('duration', 0)
        file_size = result.get('file_size', 0)
        source = result.get('source', 'Unknown')
        elapsed_time = result.get('elapsed', 0)
        
        # تنسيق المدة
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
        
        # تنسيق حجم الملف
        if file_size > 0:
            if file_size >= 1024*1024:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            else:
                size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = "غير معروف"
        
        # إنشاء هاش متقدم للبحث السريع
        title_normalized = normalize_search_text(title)
        uploader_normalized = normalize_search_text(uploader)
        query_normalized = normalize_search_text(query)
        
        # هاش مركب للبحث السريع
        search_data = f"{title_normalized}|{uploader_normalized}|{query_normalized}"
        search_hash = hashlib.md5(search_data.encode()).hexdigest()[:12]
        
        # إنشاء كلمات مفتاحية شاملة
        all_keywords = set()
        all_keywords.update(title_normalized.split())
        all_keywords.update(uploader_normalized.split())
        all_keywords.update(query_normalized.split())
        
        # إضافة كلمات مفتاحية إضافية ذكية
        if 'حبيبتي' in query_normalized or 'حبيبي' in query_normalized:
            all_keywords.add('حب')
            all_keywords.add('رومانسي')
        if 'اغنية' in query_normalized or 'أغنية' in query_normalized:
            all_keywords.add('موسيقى')
            all_keywords.add('غناء')
        
        keywords_vector = ' '.join(sorted(all_keywords))
        
        # النص المفصل والذكي للتخزين
        cache_text = f"""🎵 **{title[:80]}**
🎤 **{uploader[:50]}**
⏱️ **{duration_str}** ({duration}s) | 📊 **{size_str}**

🔍 **البحث الأصلي:** `{query[:100]}`
🏷️ **الكلمات المفتاحية:** `{keywords_vector[:200]}`
🔗 **المصدر:** {source}
⚡ **وقت التحميل:** {elapsed_time:.1f}s

📊 **هاش البحث:** `{search_hash}`
📅 **تاريخ التخزين:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🆔 **معرف الملف:** `{os.path.basename(file_path)}`

🤖 **بواسطة:** ZeMusic Smart Cache System V2
🔄 **للبحث السريع:** استخدم أي من الكلمات أعلاه

#تخزين_ذكي #موسيقى #فهرسة_متقدمة
#{title_normalized.replace(' ', '_')[:30]} #{uploader_normalized.replace(' ', '_')[:20]}
#{query_normalized.replace(' ', '_')[:30]} #هاش_{search_hash}"""
        
        try:
            # رفع الملف في الخلفية لتحسين السرعة
            import asyncio
            
            async def upload_to_storage():
                try:
                    sent_message = await bot_client.send_file(
                        cache_channel,
                        file_path,
                        caption=cache_text,
                        thumb=thumb_path,
                        attributes=[
                            DocumentAttributeAudio(
                                duration=duration,
                                title=title[:64],
                                performer=uploader[:64]
                            )
                        ],
                        supports_streaming=True,
                        force_document=False
                    )
                    return sent_message
                except Exception as e:
                    LOGGER(__name__).warning(f"⚠️ فشل رفع الملف لقناة التخزين: {e}")
                    return None
            
            # تشغيل الرفع في الخلفية
            upload_task = asyncio.create_task(upload_to_storage())
            sent_message = await upload_task
            
            if thumb_path:
                LOGGER(__name__).info(f"✅ تم رفع الملف مع الصورة المصغرة لقناة التخزين: {title[:30]}")
            else:
                LOGGER(__name__).info(f"✅ تم رفع الملف لقناة التخزين: {title[:30]}")
            
            # حفظ معلومات مفصلة في قاعدة البيانات
            if sent_message and sent_message.file:
                # إعداد البيانات المحسنة لقاعدة البيانات
                enhanced_info = {
                    'title': title,
                    'uploader': uploader,
                    'duration': duration,
                    'file_size': sent_message.file.size or file_size,
                    'source': source,
                    'search_hash': search_hash,
                    'keywords_vector': keywords_vector,
                    'original_query': query,
                    'upload_time': datetime.now().isoformat()
                }
                
                # حفظ في قاعدة البيانات في الخلفية لتحسين السرعة
                async def save_to_db():
                    try:
                        success = await save_to_database_cache_enhanced(
                            sent_message.file.id,
                            getattr(sent_message.file, 'unique_id', None),
                            sent_message.id,
                            enhanced_info,
                            query
                        )
                        if success:
                            LOGGER(__name__).info(f"💾 تم حفظ البيانات المحسنة في قاعدة البيانات")
                        else:
                            LOGGER(__name__).warning(f"⚠️ فشل حفظ البيانات في قاعدة البيانات")
                    except Exception as e:
                        LOGGER(__name__).warning(f"⚠️ خطأ في حفظ قاعدة البيانات: {e}")
                
                # تشغيل الحفظ في الخلفية
                asyncio.create_task(save_to_db())
            
            LOGGER(__name__).info(f"🎯 تم حفظ الملف بنجاح مع فهرسة شاملة: {os.path.basename(file_path)}")
            return True
            
        except Exception as upload_error:
            LOGGER(__name__).error(f"❌ خطأ في رفع الملف: {upload_error}")
            return False
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في حفظ التخزين الذكي المحسن: {e}")
        return False

async def save_to_database_cache_enhanced(file_id: str, file_unique_id: str, message_id: int, enhanced_info: Dict, query: str) -> bool:
    """حفظ معلومات الملف المحسنة في قاعدة البيانات الذكية"""
    try:
        # استخراج البيانات المحسنة
        title = enhanced_info.get('title', 'Unknown')
        artist = enhanced_info.get('uploader', 'Unknown')
        duration = enhanced_info.get('duration', 0)
        file_size = enhanced_info.get('file_size', 0)
        source = enhanced_info.get('source', 'Unknown')
        search_hash = enhanced_info.get('search_hash', '')
        keywords_vector = enhanced_info.get('keywords_vector', '')
        original_query = enhanced_info.get('original_query', query)
        
        # تطبيع النصوص
        title_normalized = normalize_search_text(title)
        artist_normalized = normalize_search_text(artist)
        
        # إنشاء هاش بحث إضافي
        combined_hash = hashlib.md5((title_normalized + artist_normalized + original_query).encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # التحقق من وجود السجل أولاً
        cursor.execute("SELECT id FROM channel_index WHERE message_id = ? OR search_hash = ?", 
                      (message_id, search_hash))
        existing = cursor.fetchone()
        
        if existing:
            # تحديث السجل الموجود
            cursor.execute("""
                UPDATE channel_index 
                SET file_id = ?, file_unique_id = ?, title_normalized = ?, 
                    artist_normalized = ?, keywords_vector = ?, original_title = ?, 
                    original_artist = ?, duration = ?, file_size = ?, 
                    access_count = access_count + 1, popularity_rank = popularity_rank + 0.5,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE message_id = ? OR search_hash = ?
            """, (
                file_id, file_unique_id, title_normalized, artist_normalized, 
                keywords_vector, title, artist, duration, file_size, 
                message_id, search_hash
            ))
            LOGGER(__name__).info(f"🔄 تم تحديث السجل الموجود في قاعدة البيانات")
        else:
            # إدخال سجل جديد
            cursor.execute("""
                INSERT INTO channel_index 
                (message_id, file_id, file_unique_id, search_hash, title_normalized, 
                 artist_normalized, keywords_vector, original_title, original_artist, 
                 duration, file_size, access_count, popularity_rank, phonetic_hash, partial_matches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1.0, ?, ?)
            """, (
                message_id, file_id, file_unique_id, search_hash,
                title_normalized, artist_normalized, keywords_vector,
                title, artist, duration, file_size, combined_hash, original_query
            ))
            LOGGER(__name__).info(f"➕ تم إضافة سجل جديد لقاعدة البيانات")
        
        conn.commit()
        conn.close()
        
        LOGGER(__name__).info(f"✅ تم حفظ البيانات المحسنة: {title[:30]}")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في حفظ قاعدة البيانات المحسنة: {e}")
        return False

async def send_cached_audio(event, status_msg, cache_result: Dict, bot_client):
    """إرسال الملف الصوتي من التخزين الذكي"""
    try:
        await status_msg.edit("📤 **إرسال من التخزين الذكي...**")
        
        original_message = cache_result['original_message']
        
        # تحضير التسمية التوضيحية للمستخدم
        duration = cache_result.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
        
        user_caption = f"✦ @{config.BOT_USERNAME}"
        
        # إرسال الملف للمستخدم
        await event.respond(
            user_caption,
            file=original_message.file,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=cache_result.get('title', 'Unknown')[:60],
                    performer=cache_result.get('uploader', 'Unknown')[:40]
                )
            ]
        )
        
        await status_msg.delete()
        LOGGER(__name__).info(f"✅ تم إرسال الملف من التخزين الذكي")
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الملف المخزن: {e}")
        await status_msg.edit("❌ **خطأ في إرسال الملف من التخزين**")

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
            'format': 'bestaudio[filesize<30M]/best[filesize<30M]',  # حد أقصى للحجم
            'outtmpl': str(downloads_dir / f'{video_id}_api.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 20,  # وقت معقول للاستقرار
            'retries': 2,  # محاولات معقولة
            'concurrent_fragment_downloads': 2,  # تحميل متوازي معتدل
            'http_chunk_size': 5242880,  # 5MB chunks للاستقرار
            'prefer_ffmpeg': True,  # استخدام ffmpeg للسرعة
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

async def send_audio_file(event, status_msg, audio_file: str, result: dict, query: str = "", bot_client=None):
    """إرسال الملف الصوتي للمستخدم وحفظه في التخزين الذكي"""
    try:
        await status_msg.edit("📤 **جاري إرسال الملف...**")
        
        # إعداد التسمية التوضيحية
        duration = result.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "غير معروف"
        
        caption = f"✦ @{config.BOT_USERNAME}"
        
        # تحميل الصورة المصغرة إذا كانت متاحة
        thumb_path = None
        try:
            if 'thumbnail' in result and result['thumbnail']:
                thumb_path = await download_thumbnail(
                    result['thumbnail'], 
                    result.get('title', 'Unknown'), 
                    result.get('id', None)
                )
        except Exception as thumb_error:
            LOGGER(__name__).warning(f"⚠️ خطأ في تحميل الصورة المصغرة: {thumb_error}")
        
        # إرسال الملف الصوتي
        await event.respond(
            caption,
            file=audio_file,
            thumb=thumb_path,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration,
                    title=result.get('title', 'Unknown')[:60],
                    performer=result.get('uploader', 'Unknown')[:40]
                )
            ]
        )
        
        # حفظ في التخزين الذكي (في الخلفية)
        if query and bot_client:
            try:
                LOGGER(__name__).info(f"💾 جاري حفظ المقطع في قناة التخزين...")
                saved = await save_to_smart_cache(bot_client, audio_file, result, query, thumb_path)
                if saved:
                    LOGGER(__name__).info(f"✅ تم حفظ المقطع في التخزين الذكي")
                else:
                    LOGGER(__name__).warning(f"⚠️ فشل حفظ المقطع في التخزين الذكي")
            except Exception as cache_error:
                LOGGER(__name__).error(f"❌ خطأ في حفظ التخزين الذكي: {cache_error}")
        
        await status_msg.delete()
        
        # حذف الملفات المؤقتة
        await remove_temp_files(audio_file)
        
        # حذف الصورة المصغرة
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
                LOGGER(__name__).debug(f"🗑️ تم حذف الصورة المصغرة: {os.path.basename(thumb_path)}")
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ فشل حذف الصورة المصغرة: {e}")
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الملف: {e}")

async def try_alternative_downloads(video_id: str, title: str) -> Optional[Dict]:
    """محاولة طرق تحميل بديلة"""
    try:
        # محاولة 1: YouTube API
        api_result = await try_youtube_api_download(video_id, title)
        if api_result and api_result.get('success'):
            return api_result
        
        # محاولة 2: تدوير الكوكيز الذكي (الدفعة الثانية)
        cookies_files = get_available_cookies()
        
        # حساب التوزيع الديناميكي
        distribution = calculate_cookies_distribution(len(cookies_files))
        primary_count = distribution['primary']
        secondary_count = distribution['secondary']
        
        if secondary_count == 0:
            LOGGER(__name__).info("⚠️ لا توجد كوكيز ثانوية - تخطي هذه المرحلة")
            return None
        
        start_index = primary_count
        end_index = primary_count + secondary_count
        
        LOGGER(__name__).info(f"🔄 استخدام {secondary_count} كوكيز ثانوي من المؤشر {start_index} إلى {end_index}")
        
        for i, cookie_file in enumerate(cookies_files[start_index:end_index], start_index + 1):
            try:
                LOGGER(__name__).info(f"🍪 محاولة كوكيز بديل #{i}: {os.path.basename(cookie_file)}")
                
                downloads_dir = Path("downloads")
                ydl_opts = {
                    'format': 'bestaudio[filesize<25M]/best[filesize<25M]',
                    'outtmpl': str(downloads_dir / f'{video_id}_alt_{i}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'cookiefile': cookie_file,
                    'socket_timeout': 18,  # وقت معقول للاستقرار
                    'retries': 2,
                    'concurrent_fragment_downloads': 2,
                    'http_chunk_size': 4194304,  # 4MB chunks
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=True
                    )
                    
                    if info:
                        # تتبع نجاح الكوكيز
                        track_cookie_usage(cookie_file, success=True)
                        
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
                error_msg = str(e).lower()
                LOGGER(__name__).warning(f"❌ فشل الكوكيز البديل #{i}: {e}")
                
                # تتبع فشل الكوكيز وحظر المشكوك فيها
                track_cookie_usage(cookie_file, success=False)
                
                if any(keyword in error_msg for keyword in [
                    'blocked', 'forbidden', '403', 'unavailable', 'cookies', 'expired',
                    'sign in', 'login', 'authentication', 'token', 'session', 'captcha'
                ]):
                    mark_cookie_as_blocked(cookie_file, f"بديل: {str(e)[:50]}")
                
                continue
        
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في المحاولات البديلة: {e}")
        return None

async def force_download_any_way(video_id: str, title: str) -> Optional[Dict]:
    """محاولة تحميل قسري بجميع الطرق المتاحة"""
    try:
        # محاولة جميع ملفات الكوكيز المتبقية (الدفعة الأخيرة)
        cookies_files = get_available_cookies()
        
        # حساب التوزيع الديناميكي
        distribution = calculate_cookies_distribution(len(cookies_files))
        primary_count = distribution['primary']
        secondary_count = distribution['secondary']
        remaining_count = distribution['remaining']
        
        if remaining_count == 0:
            LOGGER(__name__).info("⚠️ لا توجد كوكيز متبقية للمحاولة القسرية")
            return None
        
        start_index = primary_count + secondary_count
        end_index = start_index + remaining_count
        remaining_files = cookies_files[start_index:end_index]
        
        LOGGER(__name__).info(f"🚀 محاولة قسرية مع {len(remaining_files)} ملف كوكيز متبقي (من {start_index} إلى {end_index})")
        
        for i, cookie_file in enumerate(remaining_files, start_index + 1):
            try:
                LOGGER(__name__).info(f"🚀 محاولة قسرية #{i}: {os.path.basename(cookie_file)}")
                
                downloads_dir = Path("downloads")
                ydl_opts = {
                    'format': 'bestaudio[filesize<25M]/best[filesize<25M]',  # حد أقصى للحجم
                    'outtmpl': str(downloads_dir / f'{video_id}_force_{i}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'cookiefile': cookie_file,
                    'socket_timeout': 18,  # وقت معقول
                    'retries': 2,  # محاولات معقولة
                    'ignore_errors': True,
                    'concurrent_fragment_downloads': 2,
                    'http_chunk_size': 4194304,  # 4MB chunks
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=True
                    )
                    
                    if info:
                        # تتبع نجاح الكوكيز في المحاولة القسرية
                        track_cookie_usage(cookie_file, success=True)
                        
                        for file_path in downloads_dir.glob(f"{video_id}_force_{i}.*"):
                            if file_path.exists() and file_path.stat().st_size > 1000:
                                LOGGER(__name__).info(f"🎉 نجح التحميل القسري بالكوكيز: {os.path.basename(cookie_file)}")
                                return {
                                    'success': True,
                                    'file_path': str(file_path),
                                    'title': info.get('title', title),
                                    'duration': info.get('duration', 0),
                                    'uploader': info.get('uploader', 'Unknown'),
                                    'elapsed': 0
                                }
                                
            except Exception as e:
                error_msg = str(e).lower()
                LOGGER(__name__).warning(f"❌ فشل القسري #{i}: {e}")
                
                # تتبع فشل الكوكيز وحظر التالفة نهائياً
                track_cookie_usage(cookie_file, success=False)
                
                if any(keyword in error_msg for keyword in [
                    'blocked', 'forbidden', '403', 'unavailable', 'cookies', 'expired',
                    'sign in', 'login', 'authentication', 'token', 'session', 'captcha',
                    'invalid', 'corrupt'
                ]):
                    mark_cookie_as_blocked(cookie_file, f"قسري: {str(e)[:50]}")
                    LOGGER(__name__).error(f"💀 كوكيز تالف نهائياً: {os.path.basename(cookie_file)}")
                
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

async def download_thumbnail(url: str, title: str, video_id: str = None) -> Optional[str]:
    """تحميل الصورة المصغرة بشكل غير متزامن"""
    if not url:
        return None
    
    try:
        # استخدام video_id إذا كان متاحاً، وإلا استخدام العنوان المنظف
        if video_id:
            thumb_path = f"downloads/thumb_{video_id}.jpg"
        else:
            title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
            thumb_path = f"downloads/thumb_{title_clean[:20]}.jpg"
        
        # تحقق من وجود الصورة مسبقاً
        if os.path.exists(thumb_path):
            return thumb_path
        
        LOGGER(__name__).info(f"📸 تحميل الصورة المصغرة: {os.path.basename(thumb_path)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, mode='wb') as f:
                        await f.write(await resp.read())
                    LOGGER(__name__).info(f"✅ تم تحميل الصورة المصغرة: {os.path.basename(thumb_path)}")
                    return thumb_path
                else:
                    LOGGER(__name__).warning(f"⚠️ فشل تحميل الصورة: HTTP {resp.status}")
    except Exception as e:
        LOGGER(__name__).warning(f"❌ خطأ في تحميل الصورة المصغرة: {e}")
    
    return None

async def process_unlimited_download_enhanced(event, user_id: int, start_time: float):
    """معالجة التحميل المتوازي المحسن مع ذكاء اصطناعي"""
    task_id = f"{user_id}_{int(time.time() * 1000000)}"  # دقة عالية جداً
    
    try:
        # تسجيل بداية المهمة فوراً مع معلومات إضافية
        active_downloads[task_id] = {
            'user_id': user_id,
            'start_time': start_time,
            'task_id': task_id,
            'status': 'started_enhanced',
            'phase': 'initialization'
        }
        
        LOGGER(__name__).info(f"🚀 بدء معالجة فورية محسنة للمستخدم {user_id} | المهمة: {task_id}")
        
        # تنفيذ المعالجة الكاملة المحسنة في مهمة منفصلة - بدون انتظار
        asyncio.create_task(execute_parallel_download_enhanced(event, user_id, start_time, task_id))
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في معالجة التحميل المتوازي المحسن: {e}")
        await update_performance_stats(False, time.time() - start_time)
    finally:
        # تنظيف المهمة
        if task_id in active_downloads:
            del active_downloads[task_id]
            LOGGER(__name__).info(f"🧹 تم تنظيف العملية المكتملة: {task_id} - العمليات النشطة: {len(active_downloads)}")

async def execute_parallel_download_enhanced(event, user_id: int, start_time: float, task_id: str):
    """تنفيذ التحميل المتوازي الكامل مع التحسينات الذكية"""
    try:
        # استخراج الاستعلام
        match = event.pattern_match
        if not match:
            await event.reply("❌ **خطأ في تحليل الطلب**")
            return
        
        query = match.group(2) if match.group(2) else ""
        if not query:
            await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
            await update_performance_stats(False, time.time() - start_time)
            return
        
        # تحديث حالة المهمة
        if task_id in active_downloads:
            active_downloads[task_id].update({
                'query': query,
                'status': 'processing_enhanced',
                'phase': 'search_preparation'
            })
        
        LOGGER(__name__).info(f"🎵 معالجة متوازية محسنة: {query} | المستخدم: {user_id} | المهمة: {task_id}")
        
        # تحديث المرحلة
        if task_id in active_downloads:
            active_downloads[task_id]['phase'] = 'intelligent_search'
        
        # متغير لرسالة الحالة (سيتم إنشاؤه لاحقاً عند الحاجة)
        status_msg = None
        
        # البحث في الكاش بصمت - بدون رسائل مزعجة
        # status_msg سيتم إنشاؤه عند الحاجة فقط
        
        # البحث المتوازي المحسن بدون حدود
        try:
            parallel_result = await parallel_search_with_monitoring(query, event.client)
            
            if parallel_result and parallel_result.get('success'):
                search_source = parallel_result.get('search_source', 'unknown')
                search_time = parallel_result.get('search_time', 0)
                processed_msgs = parallel_result.get('processed_messages', 0)
                
                # تحديث الإحصائيات
                await update_performance_stats(True, time.time() - start_time, from_cache=True)
                
                if search_source == 'database':
                    if not status_msg:
                        status_msg = await event.reply(f"✅ **تم العثور في الكاش المحلي ({search_time:.2f}s)**\n\n📤 **جاري الإرسال...**")
                    else:
                        await status_msg.edit(f"✅ **تم العثور في الكاش المحلي ({search_time:.2f}s)**\n\n📤 **جاري الإرسال...**")
                    success = await send_cached_from_database(event, status_msg, parallel_result, event.client)
                    if success:
                        return  # نجح الإرسال من الكاش
                    else:
                        LOGGER(__name__).warning("⚠️ فشل الإرسال من الكاش - سيتم التحميل من يوتيوب")
                elif search_source == 'smart_cache':
                    if not status_msg:
                        status_msg = await event.reply(f"✅ **تم العثور في التخزين الذكي ({search_time:.2f}s)**\n\n📤 **جاري الإرسال...**")
                    else:
                        await status_msg.edit(f"✅ **تم العثور في التخزين الذكي ({search_time:.2f}s)**\n\n📤 **جاري الإرسال...**")
                    success = await send_cached_from_telegram(event, status_msg, parallel_result, event.client)
                    if success:
                        return  # نجح الإرسال من التخزين الذكي
                    else:
                        LOGGER(__name__).warning("⚠️ فشل الإرسال من التخزين الذكي - سيتم التحميل من يوتيوب")
            else:
                # لم يتم العثور في الكاش - الانتقال مباشرة للتحميل بدون إزعاج
                pass
                
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في البحث المتوازي: {e}")
            # إزالة الرسالة المزعجة - الانتقال مباشرة للتحميل
            
        # البديل: استخدام النظام الذكي المطور
        try:
            LOGGER(__name__).info(f"🔄 استخدام النظام الذكي المطور كبديل: {query}")
            await download_song_smart(event, query)
            return
        except Exception as e:
            LOGGER(__name__).error(f"❌ فشل النظام الذكي المطور: {e}")
        
        # إذا لم يجد في التخزين، ابدأ التحميل الذكي
        if not status_msg:
            status_msg = await event.reply("🔍 **جاري البحث والتحميل من يوتيوب...**")
        else:
            await status_msg.edit("🔍 **جاري البحث والتحميل من يوتيوب...**")
        
        # تحديث المرحلة
        if task_id in active_downloads:
            active_downloads[task_id]['phase'] = 'youtube_download'
        
        # تنفيذ التحميل الذكي المحسن
        await process_smart_youtube_download(event, status_msg, query, user_id, start_time, task_id)
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في المعالجة المحسنة: {e}")
        await update_performance_stats(False, time.time() - start_time)
        
        try:
            await event.reply("❌ **حدث خطأ في معالجة طلبك المحسن**")
        except:
            pass

async def process_smart_youtube_download(event, status_msg, query: str, user_id: int, start_time: float, task_id: str):
    """معالجة التحميل الذكي من يوتيوب مع جميع التحسينات"""
    try:
        # تحديث المرحلة
        if task_id in active_downloads:
            active_downloads[task_id]['phase'] = 'youtube_search'
        
        # البحث المتقدم في يوتيوب
        await status_msg.edit("🔍 **البحث المتقدم في يوتيوب...**")
        
        # محاولة النظام المختلط أولاً (API + yt-dlp)
        try:
            from ZeMusic.plugins.play.youtube_api_downloader import search_and_download_hybrid
            hybrid_result = await search_and_download_hybrid(query)
            
            if hybrid_result and hybrid_result.get('success'):
                LOGGER(__name__).info(f"✅ نجح التحميل المختلط: {hybrid_result['title']}")
                result = {
                    'audio_path': hybrid_result['file_path'],
                    'title': hybrid_result['title'],
                    'duration': hybrid_result['duration'],
                    'uploader': hybrid_result['uploader'],
                    'video_id': hybrid_result['video_id'],
                    'method': 'hybrid_api_ytdlp'
                }
            else:
                LOGGER(__name__).info("⚠️ فشل التحميل المختلط، التبديل للنظام التقليدي")
                # استخدام النظام الموجود مع تحسينات
                result = await downloader.hyper_download(query)
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في النظام المختلط: {e}")
            # استخدام النظام الموجود مع تحسينات
            result = await downloader.hyper_download(query)
        
        if result:
            # تحديث المرحلة
            if task_id in active_downloads:
                active_downloads[task_id]['phase'] = 'sending_file'
            
            # إرسال الملف مع حفظ في التخزين الذكي
            await send_audio_file(event, status_msg, result['audio_path'], result, query, event.client)
            
            # تحديث الإحصائيات
            await update_performance_stats(True, time.time() - start_time)
            
            LOGGER(__name__).info(f"✅ تم إكمال التحميل المحسن: {query}")
        else:
            await status_msg.edit("❌ **عذراً، لم أتمكن من العثور على الأغنية**\n\n💡 **جرب:**\n• كلمات مختلفة\n• اسم الفنان\n• جزء من كلمات الأغنية")
            await update_performance_stats(False, time.time() - start_time)
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في التحميل الذكي: {e}")
        await status_msg.edit("❌ **حدث خطأ في التحميل**")
        await update_performance_stats(False, time.time() - start_time)

# --- أوامر المطور مع Telethon ---
async def cache_stats_handler(event):
    """عرض إحصائيات التخزين الذكي"""
    import config
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
    import config
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
    import config
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
    try:
        LOGGER(__name__).info("🔴 بدء إيقاف النظام...")
        if hasattr(downloader, 'conn_manager') and downloader.conn_manager:
            await downloader.conn_manager.close()
        LOGGER(__name__).info("✅ تم إيقاف جميع الموارد")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إيقاف النظام: {e}")

# تسجيل معالج الإغلاق
atexit.register(lambda: asyncio.run(shutdown_system()))

# دالة التحميل الذكي المتوازي المطور
async def download_song_smart(message, query: str):
    """
    دالة التحميل الذكي الرئيسية مع البحث المتوازي
    
    المراحل:
    1. البحث المتوازي في الكاش وقناة التخزين
    2. إرسال فوري إذا وُجد المقطع
    3. انتقال متسلسل للطرق الأخرى إذا لم يوجد
    """
    try:
        # متغير لرسالة الحالة (سيتم إنشاؤه عند الحاجة)
        status_msg = None
        
        LOGGER(__name__).info(f"🎵 بدء البحث المتوازي للاستعلام: {query}")
        
        # المرحلة 1: البحث المتوازي في الكاش وقناة التخزين
        cache_result, telegram_result = await parallel_cache_search(query, message.client)
        
        # فحص النتائج المتوازية
        if cache_result:
            LOGGER(__name__).info("✅ تم العثور على المقطع في الكاش المحلي")
            if not status_msg:
                status_msg = await message.reply("📁 **تم العثور في الكاش!**\n📤 جاري الإرسال...")
            else:
                await status_msg.edit("📁 **تم العثور في الكاش!**\n📤 جاري الإرسال...")
            
            success = await send_local_cached_audio(message, cache_result, status_msg)
            if success:
                return
                
        elif telegram_result:
            LOGGER(__name__).info("✅ تم العثور على المقطع في قناة التخزين")
            if not status_msg:
                status_msg = await message.reply("📺 **تم العثور في قناة التخزين!**\n📤 جاري الإرسال...")
            else:
                await status_msg.edit("📺 **تم العثور في قناة التخزين!**\n📤 جاري الإرسال...")
            
            success = await send_telegram_cached_audio(message, telegram_result, status_msg)
            if success:
                return
        
        # المرحلة 2: لم يتم العثور على المقطع - الانتقال للبحث الخارجي
        LOGGER(__name__).info("🔍 لم يتم العثور في الكاش - بدء البحث الخارجي")
        if not status_msg:
            status_msg = await message.reply("🔍 **جاري البحث في YouTube...**")
        else:
            await status_msg.edit("🔍 **جاري البحث في YouTube...**")
        
        # البحث المتسلسل في الطرق الخارجية
        video_info = await sequential_external_search(query)
        
        if not video_info:
            if not status_msg:
                status_msg = await message.reply(
                    "❌ **لم يتم العثور على نتائج**\n\n"
                    "💡 **جرب:**\n"
                    "• كلمات مختلفة\n"
                    "• اسم الفنان\n"
                    "• جزء من كلمات الأغنية"
                )
            else:
                await status_msg.edit(
                    "❌ **لم يتم العثور على نتائج**\n\n"
                    "💡 **جرب:**\n"
                    "• كلمات مختلفة\n"
                    "• اسم الفنان\n"
                    "• جزء من كلمات الأغنية"
                )
            return
        
        # المرحلة 3: التحميل الذكي مع cookies
        LOGGER(__name__).info(f"⬇️ بدء التحميل الذكي: {video_info.get('title', 'غير محدد')}")
        success = await smart_download_and_send(message, video_info, status_msg)
        
        if not success:
            if not status_msg:
                status_msg = await message.reply(
                    "❌ **فشل التحميل**\n\n"
                    "حدث خطأ أثناء تحميل المقطع\n"
                    "يرجى المحاولة مرة أخرى لاحقاً"
                )
            else:
                await status_msg.edit(
                    "❌ **فشل التحميل**\n\n"
                    "حدث خطأ أثناء تحميل المقطع\n"
                    "يرجى المحاولة مرة أخرى لاحقاً"
                )
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في download_song_smart: {e}")
        try:
            await message.reply(
                "❌ **خطأ في البحث**\n\n"
                "حدث خطأ أثناء معالجة طلبك\n"
                "يرجى المحاولة مرة أخرى"
            )
        except:
            pass

# === نظام البحث المتوازي المطور ===

async def parallel_cache_search(query: str, bot_client) -> Tuple[Optional[Dict], Optional[Dict]]:
    """البحث المتوازي في الكاش المحلي وقناة التخزين مع معالجة أخطاء دقيقة"""
    start_time = time.time()
    
    try:
        LOGGER(__name__).info(f"🔍 بدء البحث المتوازي: {query}")
        
        # التحقق من صحة المدخلات
        if not query or not query.strip():
            LOGGER(__name__).error("❌ خطأ: استعلام البحث فارغ")
            return None, None
            
        if not bot_client:
            LOGGER(__name__).error("❌ خطأ: عميل البوت غير متاح")
            return None, None
        
        # تنظيف الاستعلام
        cleaned_query = query.strip()
        LOGGER(__name__).debug(f"🧹 الاستعلام المنظف: {cleaned_query}")
        
        # إنشاء مهام البحث المتوازي مع معالجة أخطاء فردية
        cache_task = None
        telegram_task = None
        
        try:
            cache_task = asyncio.create_task(search_local_cache(cleaned_query))
            LOGGER(__name__).debug("✅ تم إنشاء مهمة البحث في الكاش المحلي")
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في إنشاء مهمة الكاش المحلي: {e}")
            
        try:
            telegram_task = asyncio.create_task(search_in_telegram_cache(cleaned_query, bot_client))
            LOGGER(__name__).debug("✅ تم إنشاء مهمة البحث في التليجرام")
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في إنشاء مهمة التليجرام: {e}")
        
        # التحقق من نجاح إنشاء المهام
        if not cache_task and not telegram_task:
            LOGGER(__name__).error("❌ فشل في إنشاء أي من مهام البحث")
            return None, None
        
        # انتظار النتائج مع timeout ومعالجة أخطاء متقدمة
        cache_result = None
        telegram_result = None
        
        try:
            # تنفيذ المهام المتاحة فقط
            tasks = []
            if cache_task:
                tasks.append(cache_task)
            if telegram_task:
                tasks.append(telegram_task)
            
            LOGGER(__name__).info(f"⏳ انتظار {len(tasks)} مهمة بحث مع مهلة 10 ثوان...")
            
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10.0
            )
            
            # تحليل النتائج
            result_index = 0
            if cache_task:
                cache_result = results[result_index]
                result_index += 1
                
                if isinstance(cache_result, Exception):
                    LOGGER(__name__).error(f"❌ خطأ في البحث المحلي: {cache_result}")
                    cache_result = None
                elif cache_result:
                    LOGGER(__name__).info(f"✅ نجح البحث المحلي: {cache_result.get('title', 'غير محدد')}")
                else:
                    LOGGER(__name__).debug("🔍 لم يتم العثور على نتائج في الكاش المحلي")
                    
            if telegram_task:
                telegram_result = results[result_index]
                
                if isinstance(telegram_result, Exception):
                    LOGGER(__name__).error(f"❌ خطأ في البحث في التليجرام: {telegram_result}")
                    telegram_result = None
                elif telegram_result:
                    LOGGER(__name__).info(f"✅ نجح البحث في التليجرام: {telegram_result.get('title', 'غير محدد')}")
                else:
                    LOGGER(__name__).debug("🔍 لم يتم العثور على نتائج في التليجرام")
            
        except asyncio.TimeoutError:
            LOGGER(__name__).warning("⏰ انتهت مهلة البحث المتوازي (10 ثوان)")
            
            # إلغاء المهام المعلقة
            if cache_task and not cache_task.done():
                cache_task.cancel()
                LOGGER(__name__).debug("🚫 تم إلغاء مهمة البحث المحلي")
                
            if telegram_task and not telegram_task.done():
                telegram_task.cancel()
                LOGGER(__name__).debug("🚫 تم إلغاء مهمة البحث في التليجرام")
                
        except Exception as gather_error:
            LOGGER(__name__).error(f"❌ خطأ في تجميع نتائج البحث: {gather_error}")
            import traceback
            LOGGER(__name__).error(f"📋 تفاصيل الخطأ: {traceback.format_exc()}")
        
        # تسجيل الإحصائيات
        elapsed_time = time.time() - start_time
        LOGGER(__name__).info(
            f"📊 إحصائيات البحث المتوازي:\n"
            f"   ⏱️ الوقت المستغرق: {elapsed_time:.2f} ثانية\n"
            f"   📁 الكاش المحلي: {'✅ نجح' if cache_result else '❌ فشل/فارغ'}\n"
            f"   📺 التليجرام: {'✅ نجح' if telegram_result else '❌ فشل/فارغ'}"
        )
        
        return cache_result, telegram_result
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        LOGGER(__name__).error(
            f"❌ خطأ عام في البحث المتوازي:\n"
            f"   🔍 الاستعلام: {query}\n"
            f"   ⏱️ الوقت: {elapsed_time:.2f} ثانية\n"
            f"   📋 الخطأ: {str(e)}"
        )
        import traceback
        LOGGER(__name__).error(f"📋 تفاصيل الخطأ الكاملة: {traceback.format_exc()}")
        return None, None

async def search_local_cache(query: str) -> Optional[Dict]:
    """البحث في الكاش المحلي (قاعدة البيانات) مع معالجة أخطاء دقيقة"""
    start_time = time.time()
    conn = None
    
    try:
        LOGGER(__name__).info(f"📁 بدء البحث في الكاش المحلي: {query}")
        
        # التحقق من صحة الاستعلام
        if not query or not query.strip():
            LOGGER(__name__).error("❌ خطأ: استعلام البحث فارغ في الكاش المحلي")
            return None
        
        # تنظيف النص للبحث
        try:
            normalized_query = normalize_arabic_text(query)
            LOGGER(__name__).debug(f"🧹 الاستعلام المنظف: '{normalized_query}'")
            
            if not normalized_query:
                LOGGER(__name__).warning("⚠️ الاستعلام المنظف فارغ")
                return None
                
            search_keywords = normalized_query.split()
            LOGGER(__name__).debug(f"🔑 كلمات البحث: {search_keywords}")
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في تنظيف الاستعلام: {e}")
            return None
        
        # التحقق من وجود قاعدة البيانات
        if not os.path.exists(DATABASE_PATH):
            LOGGER(__name__).warning(f"⚠️ قاعدة البيانات غير موجودة: {DATABASE_PATH}")
            return None
        
        # الاتصال بقاعدة البيانات
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=5.0)
            cursor = conn.cursor()
            LOGGER(__name__).debug("✅ تم الاتصال بقاعدة البيانات")
            
        except sqlite3.Error as db_error:
            LOGGER(__name__).error(f"❌ خطأ في الاتصال بقاعدة البيانات: {db_error}")
            return None
        
        # التحقق من وجود الجدول
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cached_audio'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                LOGGER(__name__).warning("⚠️ جدول cached_audio غير موجود")
                return None
                
            LOGGER(__name__).debug("✅ جدول cached_audio موجود")
            
        except sqlite3.Error as e:
            LOGGER(__name__).error(f"❌ خطأ في فحص الجدول: {e}")
            return None
        
        # بناء استعلام البحث المتقدم
        search_conditions = []
        search_params = []
        
        try:
            for keyword in search_keywords:
                if keyword.strip():  # تجاهل الكلمات الفارغة
                    search_conditions.append(
                        "(LOWER(title) LIKE ? OR LOWER(artist) LIKE ? OR LOWER(keywords) LIKE ?)"
                    )
                    keyword_lower = keyword.lower()
                    search_params.extend([f"%{keyword_lower}%", f"%{keyword_lower}%", f"%{keyword_lower}%"])
            
            if not search_conditions:
                LOGGER(__name__).warning("⚠️ لا توجد شروط بحث صالحة")
                return None
                
            where_clause = " AND ".join(search_conditions)
            query_sql = f"""
            SELECT video_id, title, artist, duration, file_path, thumb, message_id, keywords, created_at
            FROM cached_audio 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT 1
            """
            
            LOGGER(__name__).debug(f"📋 استعلام SQL: {query_sql}")
            LOGGER(__name__).debug(f"📋 معاملات البحث: {len(search_params)} معامل")
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في بناء استعلام البحث: {e}")
            return None
        
        # تنفيذ الاستعلام
        try:
            cursor.execute(query_sql, search_params)
            result = cursor.fetchone()
            
            if result:
                # التحقق من صحة البيانات المسترجعة
                try:
                    result_dict = {
                        "video_id": result[0] if result[0] else "unknown",
                        "title": result[1] if result[1] else "عنوان غير محدد",
                        "artist": result[2] if result[2] else "فنان غير محدد",
                        "duration": int(result[3]) if result[3] and str(result[3]).isdigit() else 0,
                        "file_path": result[4] if result[4] else None,
                        "thumb": result[5] if result[5] else None,
                        "message_id": int(result[6]) if result[6] and str(result[6]).isdigit() else None,
                        "keywords": result[7] if result[7] else "",
                        "source": "local_cache",
                        "created_at": result[8] if result[8] else "غير محدد"
                    }
                    
                    # التحقق من وجود الملف إذا كان محدداً
                    if result_dict["file_path"] and not os.path.exists(result_dict["file_path"]):
                        LOGGER(__name__).warning(f"⚠️ الملف المحفوظ غير موجود: {result_dict['file_path']}")
                        result_dict["file_path"] = None
                    
                    elapsed_time = time.time() - start_time
                    LOGGER(__name__).info(
                        f"✅ تم العثور في الكاش المحلي:\n"
                        f"   🎵 العنوان: {result_dict['title']}\n"
                        f"   👤 الفنان: {result_dict['artist']}\n"
                        f"   📁 الملف: {'✅ موجود' if result_dict['file_path'] else '❌ غير موجود'}\n"
                        f"   ⏱️ الوقت: {elapsed_time:.2f} ثانية"
                    )
                    
                    return result_dict
                    
                except Exception as e:
                    LOGGER(__name__).error(f"❌ خطأ في معالجة نتيجة البحث: {e}")
                    return None
            else:
                elapsed_time = time.time() - start_time
                LOGGER(__name__).info(f"🔍 لم يتم العثور على نتائج في الكاش المحلي (⏱️ {elapsed_time:.2f}s)")
                return None
                
        except sqlite3.Error as e:
            LOGGER(__name__).error(f"❌ خطأ في تنفيذ استعلام البحث: {e}")
            return None
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        LOGGER(__name__).error(
            f"❌ خطأ عام في البحث المحلي:\n"
            f"   🔍 الاستعلام: {query}\n"
            f"   ⏱️ الوقت: {elapsed_time:.2f} ثانية\n"
            f"   📋 الخطأ: {str(e)}"
        )
        import traceback
        LOGGER(__name__).error(f"📋 تفاصيل الخطأ الكاملة: {traceback.format_exc()}")
        return None
        
    finally:
        # إغلاق الاتصال بقاعدة البيانات
        if conn:
            try:
                conn.close()
                LOGGER(__name__).debug("🔒 تم إغلاق الاتصال بقاعدة البيانات")
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ خطأ في إغلاق قاعدة البيانات: {e}")

async def sequential_external_search(query: str) -> Optional[Dict]:
    """البحث المتسلسل في المصادر الخارجية"""
    try:
        LOGGER(__name__).info(f"🌐 بدء البحث الخارجي المتسلسل: {query}")
        
        # الطريقة 1: YouTube Search
        try:
            LOGGER(__name__).info("🔍 محاولة YouTube Search...")
            if YOUTUBE_SEARCH_AVAILABLE:
                search = YoutubeSearch(query, max_results=1)
                results = search.to_dict()
                
                if results:
                    result = results[0]
                    video_id = result.get('id', '')
                    
                    if video_id:
                        LOGGER(__name__).info(f"✅ YouTube Search نجح: {result.get('title', 'غير محدد')}")
                        return {
                            'id': video_id,
                            'title': result.get('title', 'غير محدد'),
                            'channel': result.get('channel', 'غير محدد'),
                            'duration': result.get('duration', '0:00'),
                            'views': result.get('views', 'غير محدد'),
                            'source': 'youtube_search'
                        }
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ YouTube Search فشل: {e}")
        
        # الطريقة 2: النظام المختلط (YouTube API + yt-dlp)
        try:
            LOGGER(__name__).info("🔍 محاولة النظام المختلط (YouTube API + yt-dlp)...")
            from .youtube_api_downloader import download_youtube_hybrid
            
            success, result = await download_youtube_hybrid(query, "downloads")
            if success and result:
                LOGGER(__name__).info(f"✅ النظام المختلط نجح: {result.get('title', 'غير محدد')}")
                return {
                    'id': result['video_id'],
                    'title': result['title'],
                    'channel': result.get('channel', 'غير محدد'),
                    'duration': '0:00',  # سيتم الحصول عليها من الملف
                    'views': 'غير محدد',
                    'source': 'hybrid_api_ytdlp',
                    'file_path': result['file_path'],
                    'thumbnail': result.get('thumbnail', ''),
                    'url': result['url']
                }
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ النظام المختلط فشل: {e}")
        
        # الطريقة 3: YouTube API التقليدي (إذا كان متاحاً)
        try:
            LOGGER(__name__).info("🔍 محاولة YouTube API التقليدي...")
            import config
            
            if hasattr(config, 'YOUTUBE_API_KEY') and config.YOUTUBE_API_KEY:
                # يمكن إضافة YouTube API التقليدي هنا لاحقاً
                pass
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ YouTube API فشل: {e}")
        
        # الطريقة 3: Invidious (إذا كان متاحاً)
        try:
            LOGGER(__name__).info("🔍 محاولة Invidious...")
            # يمكن إضافة Invidious هنا لاحقاً
            pass
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ Invidious فشل: {e}")
        
        LOGGER(__name__).warning("❌ فشل جميع طرق البحث الخارجي")
        return None
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في البحث الخارجي: {e}")
        return None

async def send_local_cached_audio(message, cache_result: Dict, status_msg) -> bool:
    """إرسال المقطع الصوتي من الكاش المحلي"""
    try:
        LOGGER(__name__).info(f"📤 إرسال من الكاش المحلي: {cache_result.get('title', 'غير محدد')}")
        
        file_path = cache_result.get('file_path')
        
        if file_path and os.path.exists(file_path):
            # إرسال الملف الموجود
            await message.reply(
                file=file_path,
                message=f"✦ @{config.BOT_USERNAME}",
                attributes=[
                    DocumentAttributeAudio(
                        duration=cache_result.get('duration', 0),
                        title=cache_result.get('title', 'غير محدد'),
                        performer=cache_result.get('artist', 'ZeMusic Bot')
                    )
                ]
            )
            
            await status_msg.delete()
            LOGGER(__name__).info("✅ تم إرسال المقطع من الكاش المحلي بنجاح")
            return True
            
        else:
            LOGGER(__name__).warning("⚠️ ملف الكاش المحلي غير موجود")
            return False
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال الكاش المحلي: {e}")
        return False

async def send_telegram_cached_audio(message, telegram_result: Dict, status_msg) -> bool:
    """إرسال المقطع الصوتي من قناة التخزين"""
    try:
        LOGGER(__name__).info(f"📤 إرسال من قناة التخزين: {telegram_result.get('title', 'غير محدد')}")
        
        message_id = telegram_result.get('message_id')
        file_id = telegram_result.get('file_id')
        
        if file_id:
            # إرسال بـ file_id
            await message.reply(
                file=file_id,
                message=f"✦ @{config.BOT_USERNAME}",
                attributes=[
                    DocumentAttributeAudio(
                        duration=telegram_result.get('duration', 0),
                        title=telegram_result.get('title', 'غير محدد'),
                        performer=telegram_result.get('artist', 'ZeMusic Bot')
                    )
                ]
            )
            
            await status_msg.delete()
            LOGGER(__name__).info("✅ تم إرسال المقطع من قناة التخزين بنجاح")
            return True
            
        elif message_id:
            # إعادة توجيه الرسالة
            import config
            cache_channel = config.CACHE_CHANNEL_ID
            
            await message.client.forward_messages(
                entity=message.chat_id,
                messages=message_id,
                from_peer=cache_channel
            )
            
            await status_msg.delete()
            LOGGER(__name__).info("✅ تم إعادة توجيه المقطع من قناة التخزين بنجاح")
            return True
            
        else:
            LOGGER(__name__).warning("⚠️ لا يوجد file_id أو message_id صالح")
            return False
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في إرسال من قناة التخزين: {e}")
        return False

async def smart_download_and_send(message, video_info: Dict, status_msg) -> bool:
    """التحميل الذكي مع cookies وحفظ في الكاش مع معالجة أخطاء دقيقة"""
    start_time = time.time()
    downloaded_file = None
    
    try:
        LOGGER(__name__).info(f"⬇️ بدء التحميل الذكي مع معالجة أخطاء متقدمة")
        
        # التحقق من وجود ملف محمل من النظام المختلط
        if video_info.get('source') == 'hybrid_api_ytdlp' and video_info.get('file_path'):
            hybrid_file_path = video_info.get('file_path')
            if os.path.exists(hybrid_file_path):
                LOGGER(__name__).info(f"✅ استخدام ملف محمل من النظام المختلط: {hybrid_file_path}")
                try:
                    # إرسال الملف مباشرة
                    await status_msg.edit("📤 **جاري إرسال الملف المحمل...**")
                    
                    # الحصول على معلومات الملف
                    file_size = os.path.getsize(hybrid_file_path)
                    duration = get_audio_duration(hybrid_file_path) if os.path.exists(hybrid_file_path) else 0
                    
                    # إرسال الملف
                    sent_message = await message.reply_audio(
                        audio=hybrid_file_path,
                        caption=f"🎵 **{video_info.get('title', 'أغنية')}**\n👤 **{video_info.get('channel', 'قناة')}**",
                        duration=duration,
                        title=video_info.get('title', 'أغنية'),
                        performer=video_info.get('channel', 'قناة')
                    )
                    
                    if sent_message:
                        # حفظ في قاعدة البيانات
                        await save_to_database_enhanced(
                            video_info.get('title', 'أغنية'),
                            video_info.get('id', ''),
                            sent_message.audio.file_id,
                            duration,
                            video_info.get('channel', 'قناة'),
                            video_info.get('thumbnail', ''),
                            hybrid_file_path
                        )
                        
                        await status_msg.delete()
                        LOGGER(__name__).info("✅ تم إرسال الملف من النظام المختلط بنجاح")
                        return True
                        
                except Exception as e:
                    LOGGER(__name__).warning(f"⚠️ خطأ في إرسال الملف المختلط: {e}")
                    # المتابعة للتحميل التقليدي
        
        # التحقق من صحة المدخلات
        if not video_info or not isinstance(video_info, dict):
            LOGGER(__name__).error("❌ خطأ: معلومات الفيديو غير صحيحة")
            return False
            
        if not message:
            LOGGER(__name__).error("❌ خطأ: كائن الرسالة غير متاح")
            return False
            
        if not status_msg:
            LOGGER(__name__).error("❌ خطأ: رسالة الحالة غير متاحة")
            return False
        
        # استخراج المعلومات مع التحقق من الصحة
        title = video_info.get('title', 'أغنية غير محددة').strip()
        video_id = video_info.get('id', '').strip()
        duration_text = video_info.get('duration', '0:00').strip()
        channel = video_info.get('channel', 'قناة غير محددة').strip()
        
        # التحقق من وجود video_id
        if not video_id:
            LOGGER(__name__).error("❌ خطأ: معرف الفيديو مفقود")
            return False
        
        LOGGER(__name__).info(
            f"📋 معلومات التحميل:\n"
            f"   🎵 العنوان: {title}\n"
            f"   🆔 المعرف: {video_id}\n"
            f"   👤 القناة: {channel}\n"
            f"   ⏱️ المدة: {duration_text}"
        )
        
        # تحويل المدة إلى ثوان مع معالجة أخطاء
        duration = 0
        try:
            if ':' in duration_text:
                parts = duration_text.split(':')
                if len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    
                LOGGER(__name__).debug(f"⏱️ تم تحويل المدة: {duration_text} → {duration} ثانية")
                
        except (ValueError, IndexError) as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في تحويل المدة '{duration_text}': {e}")
            duration = 0
        
        # التحقق من توفر yt-dlp
        if not yt_dlp:
            LOGGER(__name__).error("❌ خطأ: مكتبة yt-dlp غير متاحة")
            return False
        
        # الحصول على ملف cookies مع معالجة أخطاء دقيقة
        cookie_file = None
        try:
            await status_msg.edit("🍪 **جاري تحضير التحميل...**")
            LOGGER(__name__).debug("🍪 محاولة الحصول على ملف cookies")
            
            # البحث المباشر عن ملفات cookies
            cookies_dir = Path("cookies")
            if cookies_dir.exists():
                cookie_files = list(cookies_dir.glob("*.txt"))
                if cookie_files:
                    # اختيار ملف عشوائي
                    cookie_file = str(cookie_files[0])  # أول ملف متاح
                    
                    if os.path.exists(cookie_file):
                        file_size = os.path.getsize(cookie_file)
                        LOGGER(__name__).info(f"✅ تم الحصول على ملف cookies: {cookie_file} ({file_size} bytes)")
                    else:
                        LOGGER(__name__).warning("⚠️ ملف cookies غير موجود")
                        cookie_file = None
                else:
                    LOGGER(__name__).warning("⚠️ لا توجد ملفات cookies في المجلد")
                    cookie_file = None
            else:
                LOGGER(__name__).warning("⚠️ مجلد cookies غير موجود")
                cookie_file = None
            
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في الحصول على cookies: {e}")
            cookie_file = None
        
        # إعداد مجلد التحميلات مع التحقق
        try:
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            LOGGER(__name__).debug(f"📁 مجلد التحميلات جاهز: {downloads_dir.absolute()}")
            
            # التحقق من الصلاحيات
            if not os.access(downloads_dir, os.W_OK):
                LOGGER(__name__).error("❌ لا توجد صلاحية كتابة في مجلد التحميلات")
                return False
                
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في إعداد مجلد التحميلات: {e}")
            return False
        
        # إعدادات التحميل المحسنة مع تحويل إلى MP3
        try:
            ydl_opts = get_ytdlp_opts(cookie_file)
            ydl_opts['outtmpl'] = f'downloads/{video_id}.%(ext)s'
            
            # إضافة cookies إذا كان متاحاً
            if cookie_file and os.path.exists(cookie_file):
                ydl_opts['cookiefile'] = cookie_file
                LOGGER(__name__).info("🍪 تم إضافة ملف cookies لإعدادات التحميل")
            else:
                LOGGER(__name__).info("🚫 التحميل بدون cookies")
            
            LOGGER(__name__).debug(f"⚙️ إعدادات yt-dlp: {ydl_opts}")
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في إعداد خيارات التحميل: {e}")
            return False
        
        # تحديث رسالة الحالة
        try:
            await status_msg.edit("📥 **جاري التحميل من YouTube...**")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في تحديث رسالة الحالة: {e}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(video_url, download=True)
                
                # البحث عن الملف المحمل
                downloaded_file = None
                for ext in ['mp3', 'webm', 'm4a', 'ogg', 'opus']:
                    file_path = f'downloads/{video_id}.{ext}'
                    if os.path.exists(file_path):
                        downloaded_file = file_path
                        break
                
                if not downloaded_file:
                    LOGGER(__name__).error("❌ لم يتم العثور على الملف المحمل")
                    return False
                
                # تحميل الصورة المصغرة
                thumb_path = None
                try:
                    if info and 'thumbnail' in info and info['thumbnail']:
                        thumb_path = await download_thumbnail(info['thumbnail'], title, video_id)
                    elif info and 'thumbnails' in info and info['thumbnails']:
                        # أخذ أفضل جودة متاحة
                        best_thumb = None
                        for thumb in info['thumbnails']:
                            if thumb.get('url'):
                                best_thumb = thumb['url']
                        if best_thumb:
                            thumb_path = await download_thumbnail(best_thumb, title, video_id)
                except Exception as thumb_error:
                    LOGGER(__name__).warning(f"⚠️ خطأ في تحميل الصورة المصغرة: {thumb_error}")
                
                # إرسال الملف
                await status_msg.edit("📤 **جاري الإرسال...**")
                
                try:
                    LOGGER(__name__).info(f"📤 محاولة إرسال الملف: {downloaded_file}")
                    audio_message = await message.reply(
                        file=downloaded_file,
                        message=f"✦ @{config.BOT_USERNAME}",
                        thumb=thumb_path,
                        attributes=[
                            DocumentAttributeAudio(
                                duration=duration,
                                title=title,
                                performer=channel
                            )
                        ]
                    )
                    LOGGER(__name__).info(f"✅ تم إرسال الملف بنجاح: {audio_message.id}")
                except Exception as send_error:
                    LOGGER(__name__).error(f"❌ خطأ في إرسال الملف: {send_error}")
                    raise send_error
                
                # حفظ في الكاش للاستخدام المستقبلي
                await save_to_cache(video_id, title, channel, duration, downloaded_file, audio_message, thumb_path)
                
                # حذف رسالة الحالة
                try:
                    await status_msg.delete()
                except:
                    pass
                
                # حذف الملفات المؤقتة
                try:
                    os.remove(downloaded_file)
                except:
                    pass
                
                # حذف الصورة المصغرة
                if thumb_path and os.path.exists(thumb_path):
                    try:
                        os.remove(thumb_path)
                    except:
                        pass
                
                LOGGER(__name__).info(f"✅ تم إرسال وحفظ الأغنية: {title}")
                return True
                
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في التحميل مع cookies: {e}")
            
            # محاولة بدون cookies
            LOGGER(__name__).info("🔄 محاولة التحميل بدون cookies...")
            await status_msg.edit("🔄 **محاولة بديلة...**")
            
            try:
                ydl_opts_no_cookies = get_ytdlp_opts()
                ydl_opts_no_cookies['outtmpl'] = f'downloads/{video_id}_nocookies.%(ext)s'
                
                with yt_dlp.YoutubeDL(ydl_opts_no_cookies) as ydl:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    info = ydl.extract_info(video_url, download=True)
                    
                    # البحث عن الملف المحمل
                    downloaded_file = None
                    for ext in ['mp3', 'webm', 'm4a', 'ogg', 'opus']:
                        file_path = f'downloads/{video_id}_nocookies.{ext}'
                        if os.path.exists(file_path):
                            downloaded_file = file_path
                            break
                    
                    if downloaded_file:
                        # تحميل الصورة المصغرة
                        thumb_path = None
                        try:
                            if info and 'thumbnail' in info and info['thumbnail']:
                                thumb_path = await download_thumbnail(info['thumbnail'], title, video_id)
                            elif info and 'thumbnails' in info and info['thumbnails']:
                                # أخذ أفضل جودة متاحة
                                best_thumb = None
                                for thumb in info['thumbnails']:
                                    if thumb.get('url'):
                                        best_thumb = thumb['url']
                                if best_thumb:
                                    thumb_path = await download_thumbnail(best_thumb, title, video_id)
                        except Exception as thumb_error:
                            LOGGER(__name__).warning(f"⚠️ خطأ في تحميل الصورة المصغرة: {thumb_error}")
                        
                        await status_msg.edit("📤 **جاري الإرسال...**")
                        
                        audio_message = await message.reply(
                            file=downloaded_file,
                            message=f"✦ @{config.BOT_USERNAME}",
                            thumb=thumb_path,
                            attributes=[
                                DocumentAttributeAudio(
                                    duration=duration,
                                    title=title,
                                    performer=channel
                                )
                            ]
                        )
                        
                        # حفظ في الكاش
                        await save_to_cache(video_id, title, channel, duration, downloaded_file, audio_message, thumb_path)
                        
                        try:
                            await status_msg.delete()
                        except:
                            pass
                        
                        try:
                            os.remove(downloaded_file)
                        except:
                            pass
                        
                        # حذف الصورة المصغرة
                        if thumb_path and os.path.exists(thumb_path):
                            try:
                                os.remove(thumb_path)
                            except:
                                pass
                        
                        LOGGER(__name__).info(f"✅ تم إرسال الأغنية بدون cookies: {title}")
                        return True
                        
            except Exception as e2:
                LOGGER(__name__).error(f"❌ فشل التحميل بدون cookies أيضاً: {e2}")
                return False
        
        return False
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ عام في التحميل الذكي: {e}")
        return False

async def save_to_cache(video_id: str, title: str, artist: str, duration: int, file_path: str, audio_message, thumb_path: str = None) -> bool:
    """حفظ المقطع في الكاش المحلي وقناة التخزين"""
    try:
        LOGGER(__name__).info(f"💾 حفظ في الكاش: {title}")
        
        # حفظ في قاعدة البيانات المحلية
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # إدراج أو تحديث السجل
            cursor.execute("""
                INSERT OR REPLACE INTO cached_audio 
                (video_id, title, artist, duration, file_path, thumb, message_id, keywords, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                video_id,
                title,
                artist,
                duration,
                file_path,
                None,  # thumb
                getattr(audio_message, 'id', None),
                f"{title} {artist}".lower(),  # keywords
            ))
            
            conn.commit()
            conn.close()
            
            LOGGER(__name__).info("✅ تم حفظ في قاعدة البيانات المحلية")
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ خطأ في حفظ قاعدة البيانات: {e}")
        
        # حفظ في قناة التخزين (إذا كانت متاحة)
        try:
            import config
            from ZeMusic.core.telethon_client import telethon_manager
            
            if hasattr(config, 'CACHE_CHANNEL_ID') and config.CACHE_CHANNEL_ID:
                LOGGER(__name__).info(f"💾 حفظ المقطع في قناة التخزين...")
                
                # إعداد بيانات المقطع للحفظ
                result_data = {
                    'title': title,
                    'uploader': artist,
                    'duration': duration,
                    'source': 'YouTube',
                    'elapsed': 0
                }
                
                # حفظ في قناة التخزين باستخدام save_to_smart_cache
                if telethon_manager and telethon_manager.bot_client:
                    saved = await save_to_smart_cache(
                        telethon_manager.bot_client, 
                        file_path, 
                        result_data, 
                        f"{title} {artist}",
                        thumb_path  # تمرير الصورة المصغرة
                    )
                    if saved:
                        LOGGER(__name__).info("✅ تم حفظ المقطع في قناة التخزين")
                    else:
                        LOGGER(__name__).warning("⚠️ فشل حفظ المقطع في قناة التخزين")
                
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ خطأ في حفظ قناة التخزين: {e}")
        
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في حفظ الكاش: {e}")
        return False

LOGGER(__name__).info("🚀 تم تحميل نظام التحميل الذكي الخارق المتطور V2")

# إضافة نظام الفحص الدوري لقناة التخزين
LAST_CHANNEL_SYNC = 0
CHANNEL_SYNC_INTERVAL = 3600  # كل ساعة

async def sync_channel_to_database(bot_client, force_sync: bool = False) -> Dict:
    """مزامنة قناة التخزين مع قاعدة البيانات بشكل ذكي"""
    global LAST_CHANNEL_SYNC
    
    current_time = time.time()
    
    # فحص الحاجة للمزامنة
    if not force_sync and (current_time - LAST_CHANNEL_SYNC) < CHANNEL_SYNC_INTERVAL:
        return {'skipped': True, 'reason': 'لم تحن المزامنة بعد'}
    
    try:
        import config
        
        if not hasattr(config, 'CACHE_CHANNEL_ID') or not config.CACHE_CHANNEL_ID:
            return {'error': 'قناة التخزين غير محددة'}
        
        cache_channel = config.CACHE_CHANNEL_ID
        LOGGER(__name__).info(f"⚠️ مزامنة قناة التخزين معطلة مؤقتاً (قيود API للبوتات)")
        return {'error': 'مزامنة القناة معطلة مؤقتاً'}
        
        # إحصائيات المزامنة
        sync_stats = {
            'processed': 0,
            'added': 0,
            'updated': 0,
            'errors': 0,
            'start_time': current_time
        }
        
        # الحصول على آخر message_id في قاعدة البيانات
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(message_id) FROM channel_index")
        last_db_message_id = cursor.fetchone()[0] or 0
        
        LOGGER(__name__).info(f"📊 آخر رسالة في قاعدة البيانات: {last_db_message_id}")
        
        # فحص الرسائل الجديدة في القناة
        new_messages_found = 0
        batch_size = 100
        
        async for message in bot_client.iter_messages(cache_channel, limit=1000):
            if not (message.text and message.file):
                continue
                
            sync_stats['processed'] += 1
            
            # تخطي الرسائل الموجودة بالفعل
            if message.id <= last_db_message_id:
                continue
                
            new_messages_found += 1
            
            try:
                # استخراج المعلومات من الرسالة
                title = extract_title_from_cache_text(message.text)
                uploader = extract_uploader_from_cache_text(message.text)
                duration = extract_duration_from_cache_text(message.text)
                
                # استخراج هاش البحث من النص إن وجد
                import re
                hash_match = re.search(r'هاش البحث.*?`([a-f0-9]+)`', message.text)
                search_hash = hash_match.group(1) if hash_match else None
                
                # إنشاء هاش جديد إذا لم يوجد
                if not search_hash:
                    title_normalized = normalize_search_text(title)
                    uploader_normalized = normalize_search_text(uploader)
                    search_data = f"{title_normalized}|{uploader_normalized}"
                    search_hash = hashlib.md5(search_data.encode()).hexdigest()[:12]
                
                # تطبيع النصوص
                title_normalized = normalize_search_text(title)
                uploader_normalized = normalize_search_text(uploader)
                
                # إنشاء vector الكلمات المفتاحية
                keywords_vector = f"{title_normalized} {uploader_normalized}"
                
                # فحص وجود السجل
                cursor.execute("SELECT id FROM channel_index WHERE message_id = ?", (message.id,))
                existing = cursor.fetchone()
                
                if existing:
                    # تحديث السجل
                    cursor.execute("""
                        UPDATE channel_index 
                        SET file_id = ?, title_normalized = ?, artist_normalized = ?, 
                            keywords_vector = ?, original_title = ?, original_artist = ?, 
                            duration = ?, file_size = ?, search_hash = ?
                        WHERE message_id = ?
                    """, (
                        message.file.id, title_normalized, uploader_normalized,
                        keywords_vector, title, uploader, duration,
                        message.file.size or 0, search_hash, message.id
                    ))
                    sync_stats['updated'] += 1
                else:
                    # إضافة سجل جديد
                    cursor.execute("""
                        INSERT INTO channel_index 
                        (message_id, file_id, file_unique_id, search_hash, title_normalized, 
                         artist_normalized, keywords_vector, original_title, original_artist, 
                         duration, file_size, access_count, popularity_rank)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0.5)
                    """, (
                        message.id, message.file.id, getattr(message.file, 'unique_id', None),
                        search_hash, title_normalized, uploader_normalized, keywords_vector,
                        title, uploader, duration, message.file.size or 0
                    ))
                    sync_stats['added'] += 1
                
                # حفظ على دفعات
                if sync_stats['processed'] % batch_size == 0:
                    conn.commit()
                    LOGGER(__name__).info(f"💾 تم حفظ دفعة: {sync_stats['processed']} رسالة معالجة")
                
            except Exception as msg_error:
                sync_stats['errors'] += 1
                LOGGER(__name__).warning(f"⚠️ خطأ في معالجة رسالة {message.id}: {msg_error}")
                continue
        
        # حفظ نهائي
        conn.commit()
        conn.close()
        
        # تحديث وقت آخر مزامنة
        LAST_CHANNEL_SYNC = current_time
        
        # حساب الإحصائيات النهائية
        sync_stats['duration'] = time.time() - current_time
        sync_stats['new_messages'] = new_messages_found
        
        LOGGER(__name__).info(
            f"✅ اكتملت مزامنة القناة: "
            f"معالج={sync_stats['processed']} | "
            f"جديد={sync_stats['added']} | "
            f"محدث={sync_stats['updated']} | "
            f"أخطاء={sync_stats['errors']} | "
            f"مدة={sync_stats['duration']:.2f}s"
        )
        
        return sync_stats
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في مزامنة القناة: {e}")
        return {'error': str(e)}

async def auto_sync_channel_if_needed(bot_client):
    """فحص تلقائي للحاجة لمزامنة القناة"""
    try:
        # فحص آخر مزامنة
        current_time = time.time()
        if (current_time - LAST_CHANNEL_SYNC) > CHANNEL_SYNC_INTERVAL:
            LOGGER(__name__).info("🔄 بدء المزامنة التلقائية لقناة التخزين...")
            
            # تشغيل المزامنة في الخلفية
            asyncio.create_task(sync_channel_to_database(bot_client, force_sync=False))
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في المزامنة التلقائية: {e}")

async def force_channel_sync_handler(event):
    """معالج أمر المطور لإجبار مزامنة القناة"""
    import config
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        await event.reply("🔄 **بدء مزامنة قناة التخزين...**")
        
        result = await sync_channel_to_database(event.client, force_sync=True)
        
        if 'error' in result:
            await event.reply(f"❌ **خطأ في المزامنة:** {result['error']}")
        elif 'skipped' in result:
            await event.reply(f"⏭️ **تم تخطي المزامنة:** {result['reason']}")
        else:
            response = f"""✅ **اكتملت مزامنة القناة!**

📊 **الإحصائيات:**
• رسائل معالجة: {result['processed']}
• سجلات جديدة: {result['added']}
• سجلات محدثة: {result['updated']}
• أخطاء: {result['errors']}
• رسائل جديدة: {result['new_messages']}
• المدة: {result['duration']:.2f}s

💾 تم تحديث قاعدة البيانات بنجاح"""
            
            await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ **خطأ:** {e}")

# تحديث معالج البحث ليشمل المزامنة التلقائية

# إضافة دالة فحص قناة التخزين
async def verify_cache_channel(bot_client) -> Dict:
    """فحص والتحقق من صحة قناة التخزين"""
    try:
        import config
        
        # فحص وجود التعريف
        if not hasattr(config, 'CACHE_CHANNEL_ID') or not config.CACHE_CHANNEL_ID:
            return {
                'status': 'error',
                'message': 'قناة التخزين غير محددة في config.py',
                'solution': 'تأكد من تعيين CACHE_CHANNEL_USERNAME في متغيرات البيئة'
            }
        
        cache_channel = config.CACHE_CHANNEL_ID
        
        # فحص نوع المعرف
        channel_type = "unknown"
        if cache_channel.startswith('@'):
            channel_type = "username"
        elif cache_channel.startswith('-100'):
            channel_type = "supergroup_id"
        elif cache_channel.startswith('-'):
            channel_type = "group_id"
        elif cache_channel.isdigit():
            channel_type = "user_id"
        
        LOGGER(__name__).info(f"🔍 فحص قناة التخزين: {cache_channel} (نوع: {channel_type})")
        
        # محاولة الوصول للقناة
        try:
            entity = await bot_client.get_entity(cache_channel)
            
            # الحصول على معلومات القناة
            channel_info = {
                'status': 'success',
                'channel_id': cache_channel,
                'channel_type': channel_type,
                'entity_id': entity.id,
                'title': getattr(entity, 'title', 'Unknown'),
                'username': getattr(entity, 'username', None),
                'participants_count': getattr(entity, 'participants_count', 0),
                'is_channel': hasattr(entity, 'broadcast'),
                'is_megagroup': getattr(entity, 'megagroup', False),
                'access_hash': getattr(entity, 'access_hash', None)
            }
            
            # فحص صلاحيات الإرسال
            try:
                # محاولة إرسال رسالة اختبار
                test_message = await bot_client.send_message(
                    entity, 
                    "🧪 **اختبار قناة التخزين الذكي**\n\n✅ البوت يمكنه الإرسال بنجاح!\n\n🗑️ سيتم حذف هذه الرسالة خلال 10 ثوان..."
                )
                
                # حذف الرسالة بعد 10 ثوان
                await asyncio.sleep(10)
                await test_message.delete()
                
                channel_info['can_send'] = True
                channel_info['permissions'] = 'full'
                
            except Exception as perm_error:
                channel_info['can_send'] = False
                channel_info['permissions'] = 'limited'
                channel_info['permission_error'] = str(perm_error)
            
            # فحص عدد الرسائل الموجودة
            try:
                message_count = 0
                audio_count = 0
                
                async for message in bot_client.iter_messages(entity, limit=100):
                    message_count += 1
                    if message.file and message.file.mime_type and 'audio' in message.file.mime_type:
                        audio_count += 1
                
                channel_info['recent_messages'] = message_count
                channel_info['recent_audio_files'] = audio_count
                
            except Exception as count_error:
                channel_info['recent_messages'] = 0
                channel_info['recent_audio_files'] = 0
                channel_info['count_error'] = str(count_error)
            
            LOGGER(__name__).info(f"✅ قناة التخزين متاحة: {channel_info['title']}")
            return channel_info
            
        except Exception as access_error:
            return {
                'status': 'error',
                'channel_id': cache_channel,
                'channel_type': channel_type,
                'message': f'لا يمكن الوصول لقناة التخزين: {access_error}',
                'solutions': [
                    'تأكد من أن البوت عضو في القناة',
                    'تأكد من أن البوت لديه صلاحية الإرسال',
                    'تأكد من صحة معرف/يوزر القناة',
                    'تأكد من أن القناة موجودة وليست محذوفة'
                ]
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f'خطأ في فحص قناة التخزين: {e}',
            'solution': 'تحقق من إعدادات config.py'
        }

async def cache_channel_info_handler(event):
    """معالج أمر المطور لعرض معلومات قناة التخزين"""
    import config
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        await event.reply("🔍 **جاري فحص قناة التخزين...**")
        
        # فحص القناة
        result = await verify_cache_channel(event.client)
        
        if result['status'] == 'error':
            error_msg = f"❌ **خطأ في قناة التخزين**\n\n"
            error_msg += f"**المشكلة:** {result['message']}\n\n"
            
            if 'solutions' in result:
                error_msg += "**الحلول المقترحة:**\n"
                for i, solution in enumerate(result['solutions'], 1):
                    error_msg += f"{i}. {solution}\n"
            elif 'solution' in result:
                error_msg += f"**الحل:** {result['solution']}\n"
            
            await event.reply(error_msg)
        else:
            # إعداد رسالة النجاح
            success_msg = f"✅ **معلومات قناة التخزين**\n\n"
            success_msg += f"🏷️ **العنوان:** {result['title']}\n"
            success_msg += f"🆔 **المعرف:** `{result['channel_id']}`\n"
            success_msg += f"🔢 **ID الحقيقي:** `{result['entity_id']}`\n"
            
            if result.get('username'):
                success_msg += f"👤 **اليوزر:** @{result['username']}\n"
            
            success_msg += f"📊 **النوع:** {result['channel_type']}\n"
            success_msg += f"👥 **الأعضاء:** {result.get('participants_count', 'غير معروف')}\n"
            success_msg += f"📺 **قناة:** {'نعم' if result.get('is_channel') else 'لا'}\n"
            success_msg += f"🔓 **مجموعة كبيرة:** {'نعم' if result.get('is_megagroup') else 'لا'}\n\n"
            
            # صلاحيات الإرسال
            if result.get('can_send'):
                success_msg += "✅ **الصلاحيات:** البوت يمكنه الإرسال\n"
            else:
                success_msg += "❌ **الصلاحيات:** البوت لا يمكنه الإرسال\n"
                if 'permission_error' in result:
                    success_msg += f"**السبب:** {result['permission_error']}\n"
            
            # إحصائيات المحتوى
            success_msg += f"\n📈 **إحصائيات المحتوى:**\n"
            success_msg += f"• رسائل حديثة: {result.get('recent_messages', 0)}\n"
            success_msg += f"• ملفات صوتية: {result.get('recent_audio_files', 0)}\n"
            
            # إضافة معلومات من قاعدة البيانات
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM channel_index")
                total_cached = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM channel_index WHERE last_accessed > datetime('now', '-7 days')")
                recent_accessed = cursor.fetchone()[0]
                
                conn.close()
                
                success_msg += f"\n💾 **قاعدة البيانات:**\n"
                success_msg += f"• إجمالي المحفوظ: {total_cached}\n"
                success_msg += f"• استُخدم مؤخراً: {recent_accessed}\n"
                
            except Exception as db_error:
                success_msg += f"\n⚠️ **قاعدة البيانات:** خطأ في القراءة\n"
            
            await event.reply(success_msg)
        
    except Exception as e:
        await event.reply(f"❌ **خطأ:** {e}")

async def test_cache_channel_handler(event):
    """معالج أمر المطور لاختبار قناة التخزين"""
    import config
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        await event.reply("🧪 **بدء اختبار قناة التخزين...**")
        
        # فحص القناة أولاً
        result = await verify_cache_channel(event.client)
        
        if result['status'] == 'error':
            await event.reply(f"❌ **فشل الاختبار:** {result['message']}")
            return
        
        # اختبار حفظ ملف تجريبي
        import tempfile
        import os
        
        # إنشاء ملف صوتي تجريبي
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            # كتابة بيانات تجريبية (ملف فارغ)
            temp_file.write(b'test audio data')
            temp_path = temp_file.name
        
        try:
            # محاولة حفظ في التخزين الذكي
            test_result = {
                'title': 'اختبار النظام الذكي',
                'uploader': 'ZeMusic Test Bot',
                'duration': 30,
                'file_size': 1024,
                'source': 'test_system',
                'elapsed': 0.5
            }
            
            success = await save_to_smart_cache(
                event.client, 
                temp_path, 
                test_result, 
                'اختبار النظام',
                None  # لا توجد صورة مصغرة في الاختبار
            )
            
            if success:
                await event.reply("✅ **نجح الاختبار!**\n\n🎯 تم حفظ ملف تجريبي بنجاح\n💾 قاعدة البيانات محدثة\n🚀 النظام جاهز للعمل")
            else:
                await event.reply("❌ **فشل الاختبار:** لم يتم حفظ الملف التجريبي")
            
        finally:
            # حذف الملف التجريبي
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        await event.reply(f"❌ **خطأ في الاختبار:** {e}")
        import traceback
        LOGGER(__name__).error(f"خطأ في اختبار القناة: {traceback.format_exc()}")

# تحديث معالج البحث ليشمل فحص القناة التلقائي

async def smart_download_handler(event):
    """المعالج الذكي للتحميل الفوري المتوازي مع مزامنة تلقائية وفحص القناة"""
    start_time = time.time()
    user_id = event.sender_id
    
    try:
        # تتبع معدل الطلبات (للإحصائيات فقط)
        await check_rate_limit(user_id)
        
        # تهيئة قاعدة البيانات إذا لم تكن مهيأة
        await ensure_database_initialized()
        
        # فحص قناة التخزين بشكل دوري (كل 50 طلب)
        if PERFORMANCE_STATS['total_requests'] % 50 == 0:
            asyncio.create_task(verify_cache_channel_periodic(event.client))
        
        # المزامنة التلقائية لقناة التخزين (في الخلفية)
        asyncio.create_task(auto_sync_channel_if_needed(event.client))
        
        # تنظيف دوري للكوكيز المحظورة (كل 100 طلب)
        if PERFORMANCE_STATS['total_requests'] % 100 == 0:
            cleanup_blocked_cookies()
        
        # عرض إحصائيات الأداء (كل 50 طلب)
        if PERFORMANCE_STATS['total_requests'] % 50 == 0:
            log_performance_stats()
        
        # فحص الصلاحيات
        chat_id = event.chat_id
        if chat_id > 0:  # محادثة خاصة
            if not await is_search_enabled1():
                await event.reply("⟡ عذراً عزيزي اليوتيوب معطل من قبل المطور")
                return
        else:  # مجموعة أو قناة
            if not await is_search_enabled(chat_id):
                await event.reply("⟡ عذراً عزيزي اليوتيوب معطل من قبل المطور")
                return
                
        # معالجة فورية بدون حدود مع تحسينات إضافية
        LOGGER(__name__).info(f"🚀 معالجة ذكية محسنة للمستخدم {user_id} - العمليات النشطة: {len(active_downloads)}")
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في فحص الحمولة المحسن: {e}")
        await update_performance_stats(False, time.time() - start_time)
        return
    
    # تنظيف دوري للعمليات القديمة (كل 50 طلب)
    # if len(active_downloads) % 50 == 0:
    #     asyncio.create_task(cleanup_old_downloads())
    
    # تحكم ذكي في العمليات المتوازية
    current_downloads = len(active_downloads)
    
    if current_downloads < MAX_CONCURRENT_DOWNLOADS:
        # تنفيذ المعالجة الفورية المتوازية المحسنة
        asyncio.create_task(process_unlimited_download_enhanced(event, user_id, start_time))
        LOGGER(__name__).info(f"⚡ تم إنشاء مهمة متوازية محسنة للمستخدم {user_id} - العمليات النشطة: {current_downloads + 1}")
    else:
        # إذا تجاوزنا الحد، ننتظر قليلاً ثم نحاول مرة أخرى
        LOGGER(__name__).info(f"⏳ تأجيل الطلب - العمليات النشطة: {current_downloads} (الحد الأقصى: {MAX_CONCURRENT_DOWNLOADS})")
        
        async def delayed_process():
            await asyncio.sleep(0.5)  # انتظار نصف ثانية
            if len(active_downloads) < MAX_CONCURRENT_DOWNLOADS:
                await process_unlimited_download_enhanced(event, user_id, start_time)
            else:
                # إذا لا يزال مزدحماً، ننشئ المهمة بأي حال
                asyncio.create_task(process_unlimited_download_enhanced(event, user_id, start_time))
        
        asyncio.create_task(delayed_process())

async def cleanup_old_downloads():
    """تنظيف دوري للعمليات القديمة لمنع تراكمها"""
    try:
        current_time = time.time()
        old_tasks = []
        
        for task_id, task_info in active_downloads.items():
            # إذا مرت أكثر من 10 دقائق على العملية، احذفها
            if current_time - task_info.get('start_time', current_time) > 600:
                old_tasks.append(task_id)
        
        for task_id in old_tasks:
            del active_downloads[task_id]
            LOGGER(__name__).info(f"🧹 تم تنظيف عملية قديمة: {task_id}")
            
        if old_tasks:
            LOGGER(__name__).info(f"🧹 تم تنظيف {len(old_tasks)} عملية قديمة - العمليات النشطة: {len(active_downloads)}")
            
    except Exception as e:
        LOGGER(__name__).warning(f"⚠️ خطأ في تنظيف العمليات القديمة: {e}")

async def verify_cache_channel_periodic(bot_client):
    """فحص دوري لقناة التخزين في الخلفية"""
    try:
        result = await verify_cache_channel(bot_client)
        
        if result['status'] == 'error':
            LOGGER(__name__).warning(f"⚠️ مشكلة في قناة التخزين: {result['message']}")
        else:
            LOGGER(__name__).info(f"✅ قناة التخزين تعمل بشكل طبيعي: {result['title']}")
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في الفحص الدوري لقناة التخزين: {e}")

# إضافة دالة لعرض حالة النظام الشاملة
async def system_status_handler(event):
    """معالج أمر المطور لعرض حالة النظام الشاملة"""
    import config
    if event.sender_id != config.OWNER_ID:
        return
    
    try:
        await event.reply("📊 **جاري فحص حالة النظام الشاملة...**")
        
        # فحص قناة التخزين
        cache_status = await verify_cache_channel(event.client)
        
        # فحص قاعدة البيانات
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM channel_index")
            total_cached = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM channel_index WHERE last_accessed > datetime('now', '-1 day')")
            daily_accessed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM channel_index WHERE created_at > datetime('now', '-1 day')")
            daily_added = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(popularity_rank) FROM channel_index")
            avg_popularity = cursor.fetchone()[0] or 0
            
            conn.close()
            
            db_status = {
                'working': True,
                'total_cached': total_cached,
                'daily_accessed': daily_accessed,
                'daily_added': daily_added,
                'avg_popularity': avg_popularity
            }
            
        except Exception as db_error:
            db_status = {
                'working': False,
                'error': str(db_error)
            }
        
        # فحص ملفات الكوكيز
        cookies_stats = get_cookies_statistics()
        
        # إعداد رسالة الحالة الشاملة
        status_msg = "📊 **حالة النظام الشاملة**\n\n"
        
        # حالة قناة التخزين
        if cache_status['status'] == 'success':
            status_msg += f"✅ **قناة التخزين:** تعمل بشكل طبيعي\n"
            status_msg += f"   📝 العنوان: {cache_status['title']}\n"
            status_msg += f"   🎵 ملفات صوتية: {cache_status.get('recent_audio_files', 0)}\n"
            status_msg += f"   📤 صلاحية الإرسال: {'✅' if cache_status.get('can_send') else '❌'}\n"
        else:
            status_msg += f"❌ **قناة التخزين:** مشكلة\n"
            status_msg += f"   ⚠️ {cache_status['message']}\n"
        
        status_msg += "\n"
        
        # حالة قاعدة البيانات
        if db_status['working']:
            status_msg += f"✅ **قاعدة البيانات:** تعمل بشكل طبيعي\n"
            status_msg += f"   💾 إجمالي المحفوظ: {db_status['total_cached']}\n"
            status_msg += f"   📈 استُخدم اليوم: {db_status['daily_accessed']}\n"
            status_msg += f"   ➕ أُضيف اليوم: {db_status['daily_added']}\n"
            status_msg += f"   ⭐ متوسط الشعبية: {db_status['avg_popularity']:.2f}\n"
        else:
            status_msg += f"❌ **قاعدة البيانات:** مشكلة\n"
            status_msg += f"   ⚠️ {db_status['error']}\n"
        
        status_msg += "\n"
        
        # حالة ملفات الكوكيز
        if cookies_stats:
            status_msg += f"🍪 **ملفات الكوكيز:**\n"
            status_msg += f"   📊 الإجمالي: {cookies_stats.get('total', 0)}\n"
            status_msg += f"   ✅ المتاح: {cookies_stats.get('available', 0)}\n"
            status_msg += f"   🚫 المحظور: {cookies_stats.get('blocked', 0)}\n"
            status_msg += f"   🏆 الأكثر استخداماً: {cookies_stats.get('most_used_file', 'لا يوجد')}\n"
        else:
            status_msg += f"❌ **ملفات الكوكيز:** غير متاحة\n"
        
        status_msg += "\n"
        
        # إحصائيات الأداء
        stats = PERFORMANCE_STATS
        success_rate = (stats['successful_downloads'] / max(stats['total_requests'], 1)) * 100
        cache_hit_rate = (stats['cache_hits'] / max(stats['total_requests'], 1)) * 100
        
        status_msg += f"⚡ **الأداء:**\n"
        status_msg += f"   🔢 إجمالي الطلبات: {stats['total_requests']}\n"
        status_msg += f"   ✅ نسبة النجاح: {success_rate:.1f}%\n"
        status_msg += f"   💾 نسبة الكاش: {cache_hit_rate:.1f}%\n"
        status_msg += f"   ⏱️ متوسط الوقت: {stats['avg_response_time']:.2f}s\n"
        status_msg += f"   🔄 العمليات النشطة: {stats['current_concurrent']}\n"
        status_msg += f"   🏔️ الذروة: {stats['peak_concurrent']}\n"
        
        # إضافة معلومات النظام
        import psutil
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        status_msg += f"\n🖥️ **النظام:**\n"
        status_msg += f"   🧠 الذاكرة: {memory.percent}% ({memory.used//1024//1024}MB)\n"
        status_msg += f"   ⚙️ المعالج: {cpu}%\n"
        status_msg += f"   🕐 وقت التشغيل: {time.time() - start_time:.0f}s\n"
        
        await event.reply(status_msg)
        
    except Exception as e:
        await event.reply(f"❌ **خطأ في فحص النظام:** {e}")
        import traceback
        LOGGER(__name__).error(f"خطأ في فحص حالة النظام: {traceback.format_exc()}")
