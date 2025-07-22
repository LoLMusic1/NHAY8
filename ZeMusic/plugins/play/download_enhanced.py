# -*- coding: utf-8 -*-
"""
🚀 نظام التحميل الذكي المطور - موحد لجميع أنواع المحادثات مع Telethon
=====================================================

يدمج بين:
- تدوير الكوكيز والمفاتيح التلقائي المحسن
- تخزين ذكي في قناة تيليجرام مع فهرسة متقدمة
- بحث فائق السرعة في قاعدة البيانات مع AI matching
- تحميل متوازي لا محدود مع load balancing
- تبديل خاطف بين طرق التحميل مع fallback ذكي
- دعم كامل لـ Telethon مع error handling محسن
- نظام تقييم الأداء التلقائي
"""

import os
import re
import asyncio
import logging
import time
import sqlite3
import hashlib
import json
import concurrent.futures
from typing import Dict, Optional, List, Union
from itertools import cycle
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import aiofiles

# استيراد المكتبات مع معالجة الأخطاء المحسنة
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    yt_dlp = None
    YT_DLP_AVAILABLE = False
    
try:
    from youtube_search import YoutubeSearch
    YOUTUBE_SEARCH_AVAILABLE = True
except ImportError:
    try:
        from youtubesearchpython import VideosSearch
        YoutubeSearch = VideosSearch
        YOUTUBE_SEARCH_AVAILABLE = True
    except ImportError:
        YoutubeSearch = None
        YOUTUBE_SEARCH_AVAILABLE = False

# استيراد Telethon
from telethon import events
from telethon.types import Message
from telethon.tl.types import DocumentAttributeAudio, InputMediaUploadedDocument

import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER

# --- إعدادات النظام الذكي المحسن ---
REQUEST_TIMEOUT = 15  # زيادة المهلة قليلاً
DOWNLOAD_TIMEOUT = 180  # مهلة التحميل
MAX_SESSIONS = 30  # تقليل عدد الجلسات لتحسين الاستقرار
MAX_CONCURRENT_DOWNLOADS = 5  # حد أقصى للتحميلات المتزامنة

# إعدادات متقدمة
RETRY_ATTEMPTS = 3
BACKOFF_FACTOR = 2
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB حد أقصى

# قناة التخزين الذكي (يوزر أو ID) - استخدام المعرف المعالج من config.py
SMART_CACHE_CHANNEL = getattr(config, 'CACHE_CHANNEL_ID', None)

# إعدادات العرض
channel = getattr(config, 'STORE_LINK', '')
lnk = f"https://t.me/{channel}" if channel else None

# --- تدوير المفاتيح والخوادم المحسن ---
YT_API_KEYS = getattr(config, 'YT_API_KEYS', [])
API_KEYS_CYCLE = cycle(YT_API_KEYS) if YT_API_KEYS else None

INVIDIOUS_SERVERS = getattr(config, 'INVIDIOUS_SERVERS', [
    'https://invidious.io',
    'https://yewtu.be',
    'https://vid.puffyan.us',
    'https://invidious.lunar.icu'
])
INVIDIOUS_CYCLE = cycle(INVIDIOUS_SERVERS) if INVIDIOUS_SERVERS else None

# تدوير ملفات الكوكيز المحسن
def get_cookies_files():
    """الحصول على ملفات الكوكيز المتوفرة"""
    cookies_dir = Path("cookies")
    if not cookies_dir.exists():
        return []
    
    cookies_files = []
    for file in cookies_dir.glob("cookies*.txt"):
        if file.stat().st_size > 100:  # التأكد من أن الملف ليس فارغاً
            cookies_files.append(str(file))
    
    return cookies_files

COOKIES_FILES = get_cookies_files()
COOKIES_CYCLE = cycle(COOKIES_FILES) if COOKIES_FILES else None

# --- إعدادات yt-dlp محسنة مع تحسينات الأداء ---
def get_ytdlp_opts(cookies_file=None, quality="medium"):
    """إعدادات yt-dlp محسنة مع خيارات الجودة"""
    base_opts = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": RETRY_ATTEMPTS,
        "fragment_retries": RETRY_ATTEMPTS,
        "skip_unavailable_fragments": True,
        "abort_on_unavailable_fragment": False,
        "keep_fragments": False,
        "no_cache_dir": True,
        "ignoreerrors": True,
        "socket_timeout": REQUEST_TIMEOUT,
        "force_ipv4": True,
        "concurrent_fragments": 8,
        "noprogress": True,
        "verbose": False,
        "extractaudio": True,
        "audioformat": "mp3",
        "audioquality": "192",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "referer": "https://www.youtube.com/",
    }
    
    # إعدادات الجودة
    if quality == "high":
        base_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        base_opts["audioquality"] = "320"
    elif quality == "low":
        base_opts["format"] = "worstaudio[ext=m4a]/worstaudio/worst"
        base_opts["audioquality"] = "128"
    else:  # medium
        base_opts["format"] = "bestaudio[filesize<25M]/best[filesize<25M]/bestaudio/best"
        base_opts["audioquality"] = "192"
    
    if cookies_file and os.path.exists(cookies_file):
        base_opts["cookiefile"] = cookies_file
        LOGGER(__name__).info(f"🍪 استخدام cookies: {Path(cookies_file).name}")
    
    # إضافة aria2c إذا متوفر
    import shutil
    if shutil.which("aria2c"):
        base_opts.update({
            "external_downloader": "aria2c",
            "external_downloader_args": ["-x", "8", "-s", "8", "-k", "1M"],
        })
    
    return base_opts

# إنشاء مجلد التحميلات
os.makedirs("downloads", exist_ok=True)

# --- قاعدة البيانات للفهرسة الذكية المحسنة ---
DB_FILE = "smart_cache_enhanced.db"

def init_database():
    """تهيئة قاعدة البيانات المحسنة للفهرسة الذكية"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER UNIQUE,
            file_id TEXT UNIQUE,
            file_unique_id TEXT,
            file_size INTEGER,
            
            search_hash TEXT UNIQUE,
            title_normalized TEXT,
            artist_normalized TEXT,
            keywords_vector TEXT,
            
            original_title TEXT,
            original_artist TEXT,
            duration INTEGER,
            video_id TEXT,
            
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            popularity_rank REAL DEFAULT 0,
            
            phonetic_hash TEXT,
            partial_matches TEXT,
            language_detected TEXT,
            
            download_source TEXT,
            download_quality TEXT,
            download_time REAL,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول لإحصائيات الأداء
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # إنشاء الفهارس للسرعة الخارقة المحسنة
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_search_hash ON channel_index(search_hash)",
        "CREATE INDEX IF NOT EXISTS idx_title_norm ON channel_index(title_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_artist_norm ON channel_index(artist_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_popularity ON channel_index(popularity_rank DESC)",
        "CREATE INDEX IF NOT EXISTS idx_message_id ON channel_index(message_id)",
        "CREATE INDEX IF NOT EXISTS idx_file_id ON channel_index(file_id)",
        "CREATE INDEX IF NOT EXISTS idx_video_id ON channel_index(video_id)",
        "CREATE INDEX IF NOT EXISTS idx_keywords ON channel_index(keywords_vector)",
        "CREATE INDEX IF NOT EXISTS idx_access_count ON channel_index(access_count DESC)",
        "CREATE INDEX IF NOT EXISTS idx_last_accessed ON channel_index(last_accessed DESC)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    # تهيئة إحصائيات الأداء
    methods = ['cache', 'youtube_api', 'invidious', 'ytdlp_cookies', 'ytdlp_no_cookies', 'youtube_search']
    for method in methods:
        cursor.execute(
            "INSERT OR IGNORE INTO performance_stats (method_name) VALUES (?)",
            (method,)
        )
    
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند بدء الوحدة
init_database()

class EnhancedHyperSpeedDownloader:
    """مدير التحميل فائق السرعة المطور"""
    
    def __init__(self):
        self.session_pool = []
        self.executor_pool = None
        self.active_downloads = 0
        self.download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        
        # إحصائيات الأداء الحية
        self.method_performance = {
            'cache': {'weight': 1000, 'active': True, 'avg_time': 0.001, 'success_rate': 0.95},
            'youtube_api': {'weight': 100, 'active': True, 'avg_time': 2.0, 'success_rate': 0.80},
            'invidious': {'weight': 90, 'active': True, 'avg_time': 3.0, 'success_rate': 0.70},
            'ytdlp_cookies': {'weight': 85, 'active': True, 'avg_time': 8.0, 'success_rate': 0.75},
            'ytdlp_no_cookies': {'weight': 60, 'active': True, 'avg_time': 12.0, 'success_rate': 0.50},
            'youtube_search': {'weight': 50, 'active': True, 'avg_time': 4.0, 'success_rate': 0.85}
        }
        
        # تحميل إحصائيات من قاعدة البيانات
        self.load_performance_stats()
        
        # تهيئة النظام
        asyncio.create_task(self.initialize())
    
    def load_performance_stats(self):
        """تحميل إحصائيات الأداء من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT method_name, success_count, failure_count, avg_response_time, is_active FROM performance_stats")
            stats = cursor.fetchall()
            
            for method_name, success, failure, avg_time, is_active in stats:
                if method_name in self.method_performance:
                    total = success + failure
                    success_rate = success / max(1, total)
                    
                    self.method_performance[method_name].update({
                        'avg_time': avg_time,
                        'success_rate': success_rate,
                        'active': bool(is_active)
                    })
            
            conn.close()
            LOGGER(__name__).info("📊 تم تحميل إحصائيات الأداء من قاعدة البيانات")
            
        except Exception as e:
            LOGGER(__name__).warning(f"تعذر تحميل إحصائيات الأداء: {e}")
    
    async def update_performance_stats(self, method_name: str, success: bool, response_time: float):
        """تحديث إحصائيات الأداء"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            if success:
                cursor.execute(
                    "UPDATE performance_stats SET success_count = success_count + 1, avg_response_time = (avg_response_time + ?) / 2, last_used = CURRENT_TIMESTAMP WHERE method_name = ?",
                    (response_time, method_name)
                )
            else:
                cursor.execute(
                    "UPDATE performance_stats SET failure_count = failure_count + 1, last_used = CURRENT_TIMESTAMP WHERE method_name = ?",
                    (method_name,)
                )
            
            conn.commit()
            conn.close()
            
            # تحديث الكاش المحلي
            if method_name in self.method_performance:
                if success:
                    self.method_performance[method_name]['avg_time'] = (
                        self.method_performance[method_name]['avg_time'] + response_time
                    ) / 2
                    
        except Exception as e:
            LOGGER(__name__).warning(f"فشل تحديث إحصائيات {method_name}: {e}")
    
    async def initialize(self):
        """تهيئة مجموعة الاتصالات الخارقة المحسنة"""
        try:
            connector = aiohttp.TCPConnector(
                limit=500,  # تقليل العدد قليلاً
                limit_per_host=100,
                ttl_dns_cache=600,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                force_close=False,  # تم تغييره لتجنب التعارض
                keepalive_timeout=60
            )
            
            # إنشاء جلسات HTTP محسنة
            for i in range(MAX_SESSIONS):
                session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(
                        total=REQUEST_TIMEOUT,
                        connect=5,
                        sock_read=10
                    ),
                    headers={
                        'User-Agent': f'ZeMusic-Enhanced-{i}',
                        'Accept': 'application/json,text/html,application/xhtml+xml',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                self.session_pool.append(session)
            
            # مجموعة معالجات Thread محسنة
            self.executor_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=min(50, (os.cpu_count() or 1) * 10)
            )
            
            LOGGER(__name__).info(f"🚀 تم تهيئة النظام المطور: {MAX_SESSIONS} جلسة, {self.executor_pool._max_workers} معالج")
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تهيئة النظام: {e}")
    
    def normalize_text(self, text: str) -> str:
        """تطبيع النص المحسن للبحث مع دعم محسن للعربية والإنجليزية"""
        if not text:
            return ""
        
        # تحويل للأحرف الصغيرة
        text = text.lower()
        
        # إزالة التشكيل العربي
        arabic_diacritics = re.compile(r'[ًٌٍَُِّْٰٱٲٳٴٵٶٷٸٹٺٻټٽپٿڀځڂڃڄڅچڇڈډڊڋڌڍڎڏڐڑڒړڔڕږڗژڙښڛڜڝڞڟڠڡڢڣڤڥڦڧڨکڪګڬڭڮگڰڱڲڳڴڵڶڷڸڹںڻڼڽھڿۀہۂۃۄۅۆۇۈۉۊۋیۍێۏې]')
        text = arabic_diacritics.sub('', text)
        
        # إزالة الرموز غير المرغوبة مع الاحتفاظ بالمسافات
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
        
        # تنظيف المسافات
        text = re.sub(r'\s+', ' ', text).strip()
        
        # تطبيع الحروف العربية المتشابهة
        arabic_normalizations = {
            'ة': 'ه', 'ي': 'ى', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ؤ': 'و', 'ئ': 'ي', 'ء': '', 'ـ': ''
        }
        
        for old, new in arabic_normalizations.items():
            text = text.replace(old, new)
        
        # تطبيع الحروف الإنجليزية المتشابهة
        english_normalizations = {
            'ph': 'f', 'gh': 'g', 'tion': 'shun', 'ck': 'k'
        }
        
        for old, new in english_normalizations.items():
            text = text.replace(old, new)
        
        return text
    
    def create_search_hash(self, title: str, artist: str = "") -> str:
        """إنشاء هاش محسن للبحث السريع"""
        normalized_title = self.normalize_text(title)
        normalized_artist = self.normalize_text(artist)
        combined = f"{normalized_title}_{normalized_artist}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:20]
    
    def create_keywords_vector(self, title: str, artist: str, query: str) -> str:
        """إنشاء vector للكلمات المفتاحية للبحث المتقدم"""
        all_text = f"{title} {artist} {query}"
        normalized = self.normalize_text(all_text)
        
        # تقسيم إلى كلمات وإزالة الكلمات القصيرة
        words = [word for word in normalized.split() if len(word) > 2]
        
        # إضافة الكلمات الجزئية للبحث المرن
        partial_words = []
        for word in words:
            if len(word) > 4:
                partial_words.extend([word[:3], word[:4], word[:-1]])
        
        all_keywords = words + partial_words
        return " ".join(set(all_keywords))
    
    async def lightning_search_cache(self, query: str) -> Optional[Dict]:
        """بحث خاطف محسن في الكاش مع AI matching"""
        start_time = time.time()
        
        try:
            normalized_query = self.normalize_text(query)
            search_hash = self.create_search_hash(normalized_query)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # البحث المباشر بالهاش (الأسرع)
            cursor.execute(
                """SELECT message_id, file_id, original_title, original_artist, duration, video_id, file_size 
                   FROM channel_index WHERE search_hash = ? LIMIT 1""",
                (search_hash,)
            )
            result = cursor.fetchone()
            
            if result:
                await self.update_cache_access(cursor, search_hash)
                conn.commit()
                conn.close()
                
                await self.update_performance_stats('cache', True, time.time() - start_time)
                
                return {
                    'message_id': result[0],
                    'file_id': result[1],
                    'title': result[2],
                    'artist': result[3],
                    'duration': result[4],
                    'video_id': result[5],
                    'file_size': result[6],
                    'source': 'cache_direct',
                    'cached': True,
                    'search_time': time.time() - start_time
                }
            
            # البحث التقريبي المحسن بالـ keywords
            query_words = normalized_query.split()
            like_conditions = []
            params = []
            
            for word in query_words:
                if len(word) > 2:
                    like_conditions.append("keywords_vector LIKE ?")
                    params.append(f'%{word}%')
            
            if like_conditions:
                search_sql = f"""
                    SELECT message_id, file_id, original_title, original_artist, duration, video_id, file_size,
                           access_count, popularity_rank
                    FROM channel_index 
                    WHERE ({' OR '.join(like_conditions)}) 
                       OR title_normalized LIKE ? 
                       OR artist_normalized LIKE ?
                    ORDER BY popularity_rank DESC, access_count DESC 
                    LIMIT 3
                """
                params.extend([f'%{normalized_query}%', f'%{normalized_query}%'])
                
                cursor.execute(search_sql, params)
                results = cursor.fetchall()
                
                if results:
                    # اختيار أفضل نتيجة بناء على الشعبية والدقة
                    best_result = results[0]
                    
                    await self.update_cache_access(cursor, None, best_result[0])
                    conn.commit()
                    conn.close()
                    
                    await self.update_performance_stats('cache', True, time.time() - start_time)
                    
                    return {
                        'message_id': best_result[0],
                        'file_id': best_result[1],
                        'title': best_result[2],
                        'artist': best_result[3],
                        'duration': best_result[4],
                        'video_id': best_result[5],
                        'file_size': best_result[6],
                        'source': 'cache_fuzzy',
                        'cached': True,
                        'search_time': time.time() - start_time
                    }
            
            conn.close()
            await self.update_performance_stats('cache', False, time.time() - start_time)
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث السريع: {e}")
            await self.update_performance_stats('cache', False, time.time() - start_time)
        
        return None
    
    async def update_cache_access(self, cursor, search_hash: str = None, message_id: int = None):
        """تحديث إحصائيات الوصول للكاش"""
        try:
            if search_hash:
                cursor.execute(
                    """UPDATE channel_index 
                       SET access_count = access_count + 1, 
                           last_accessed = CURRENT_TIMESTAMP,
                           popularity_rank = popularity_rank + 0.1
                       WHERE search_hash = ?""",
                    (search_hash,)
                )
            elif message_id:
                cursor.execute(
                    """UPDATE channel_index 
                       SET access_count = access_count + 1, 
                           last_accessed = CURRENT_TIMESTAMP,
                           popularity_rank = popularity_rank + 0.1
                       WHERE message_id = ?""",
                    (message_id,)
                )
        except Exception as e:
            LOGGER(__name__).warning(f"فشل تحديث إحصائيات الوصول: {e}")
    
    async def get_session(self):
        """الحصول على جلسة أقل استخداماً مع load balancing"""
        if not self.session_pool:
            await self.initialize()
        
        # اختيار جلسة عشوائية لتوزيع الحمل
        import random
        return random.choice(self.session_pool)
    
    async def youtube_api_search(self, query: str) -> Optional[Dict]:
        """البحث المحسن عبر YouTube Data API مع retry logic"""
        if not API_KEYS_CYCLE:
            return None
        
        start_time = time.time()
        session = await self.get_session()
        
        for attempt in range(len(YT_API_KEYS)):
            try:
                key = next(API_KEYS_CYCLE)
                params = {
                    "part": "snippet,contentDetails",
                    "q": query,
                    "type": "video",
                    "maxResults": 3,
                    "order": "relevance",
                    "videoDuration": "medium",
                    "key": key
                }
                
                async with session.get(
                    "https://www.googleapis.com/youtube/v3/search", 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 403:
                        LOGGER(__name__).warning(f"YouTube API key exhausted: {key[:10]}...")
                        continue
                    
                    if resp.status != 200:
                        continue
                    
                    data = await resp.json()
                    items = data.get("items", [])
                    if not items:
                        continue
                    
                    # اختيار أفضل نتيجة (الأولى عادة)
                    item = items[0]
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    
                    # محاولة الحصول على معلومات المدة
                    duration = 0
                    try:
                        details_params = {
                            "part": "contentDetails",
                            "id": video_id,
                            "key": key
                        }
                        async with session.get(
                            "https://www.googleapis.com/youtube/v3/videos",
                            params=details_params
                        ) as details_resp:
                            if details_resp.status == 200:
                                details_data = await details_resp.json()
                                if details_data.get("items"):
                                    duration_str = details_data["items"][0]["contentDetails"]["duration"]
                                    duration = self.parse_youtube_duration(duration_str)
                    except:
                        pass
                    
                    await self.update_performance_stats('youtube_api', True, time.time() - start_time)
                    
                    return {
                        "video_id": video_id,
                        "title": snippet.get("title", "")[:80],
                        "artist": snippet.get("channelTitle", "Unknown"),
                        "duration": duration,
                        "thumb": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                        "source": "youtube_api"
                    }
                    
            except asyncio.TimeoutError:
                LOGGER(__name__).warning(f"YouTube API timeout (attempt {attempt + 1})")
                continue
            except Exception as e:
                LOGGER(__name__).warning(f"فشل YouTube API: {e}")
                continue
        
        await self.update_performance_stats('youtube_api', False, time.time() - start_time)
        return None
    
    def parse_youtube_duration(self, duration_str: str) -> int:
        """تحويل مدة YouTube من ISO 8601 إلى ثوان"""
        try:
            import re
            pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
            match = pattern.match(duration_str)
            if match:
                hours, minutes, seconds = match.groups()
                total_seconds = 0
                if hours:
                    total_seconds += int(hours) * 3600
                if minutes:
                    total_seconds += int(minutes) * 60
                if seconds:
                    total_seconds += int(seconds)
                return total_seconds
        except:
            pass
        return 0
    
    async def invidious_search(self, query: str) -> Optional[Dict]:
        """البحث المحسن عبر Invidious مع fallback متعدد"""
        if not INVIDIOUS_CYCLE:
            return None
        
        start_time = time.time()
        session = await self.get_session()
        
        for attempt in range(min(3, len(INVIDIOUS_SERVERS))):
            try:
                server = next(INVIDIOUS_CYCLE)
                url = f"{server}/api/v1/search"
                params = {
                    "q": query, 
                    "type": "video",
                    "sort_by": "relevance",
                    "duration": "medium"
                }
                
                async with session.get(
                    url, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as resp:
                    if resp.status != 200:
                        LOGGER(__name__).warning(f"Invidious server {server} returned {resp.status}")
                        continue
                    
                    data = await resp.json()
                    if not isinstance(data, list):
                        continue
                    
                    # البحث عن أول فيديو صالح
                    for item in data:
                        if item.get("type") == "video" and item.get("videoId"):
                            await self.update_performance_stats('invidious', True, time.time() - start_time)
                            
                            return {
                                "video_id": item.get("videoId"),
                                "title": item.get("title", "")[:80],
                                "artist": item.get("author", "Unknown"),
                                "duration": int(item.get("lengthSeconds", 0)),
                                "thumb": self.get_best_thumbnail(item.get("videoThumbnails", [])),
                                "source": f"invidious_{server.split('//')[1]}"
                            }
                    
            except asyncio.TimeoutError:
                LOGGER(__name__).warning(f"Invidious timeout: {server}")
                continue
            except Exception as e:
                LOGGER(__name__).warning(f"فشل Invidious {server}: {e}")
                continue
        
        await self.update_performance_stats('invidious', False, time.time() - start_time)
        return None
    
    def get_best_thumbnail(self, thumbnails: list) -> Optional[str]:
        """اختيار أفضل thumbnail من القائمة"""
        if not thumbnails:
            return None
        
        # ترتيب الأولوية: maxresdefault > hqdefault > mqdefault > default
        quality_priority = ['maxresdefault', 'hqdefault', 'mqdefault', 'default']
        
        for quality in quality_priority:
            for thumb in thumbnails:
                if quality in thumb.get('url', ''):
                    return thumb['url']
        
        # إذا لم نجد، نأخذ الأخير (عادة أعلى جودة)
        return thumbnails[-1].get('url') if thumbnails else None
    
    async def youtube_search_simple(self, query: str) -> Optional[Dict]:
        """البحث المحسن عبر youtube_search"""
        if not YOUTUBE_SEARCH_AVAILABLE:
            return None
        
        start_time = time.time()
        
        try:
            loop = asyncio.get_running_loop()
            
            # تشغيل البحث في thread منفصل
            results = await loop.run_in_executor(
                self.executor_pool,
                lambda: YoutubeSearch(query, max_results=3).to_dict()
            )
            
            if not results:
                await self.update_performance_stats('youtube_search', False, time.time() - start_time)
                return None
            
            # اختيار أفضل نتيجة
            result = results[0]
            
            await self.update_performance_stats('youtube_search', True, time.time() - start_time)
            
            return {
                "video_id": result["id"],
                "title": result["title"][:80],
                "artist": result.get("channel", "Unknown"),
                "duration": self.parse_duration_string(result.get("duration", "")),
                "thumb": result["thumbnails"][0] if result.get("thumbnails") else None,
                "link": f"https://youtube.com{result['url_suffix']}",
                "source": "youtube_search"
            }
            
        except Exception as e:
            LOGGER(__name__).warning(f"فشل YouTube Search: {e}")
            await self.update_performance_stats('youtube_search', False, time.time() - start_time)
            return None
    
    def parse_duration_string(self, duration_str: str) -> int:
        """تحويل نص المدة إلى ثوان"""
        try:
            if not duration_str:
                return 0
            
            # إزالة المسافات والنصوص الإضافية
            duration_str = re.sub(r'[^\d:]', '', duration_str)
            
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                return int(duration_str) if duration_str.isdigit() else 0
        except:
            return 0
    
    async def download_with_ytdlp(self, video_info: Dict, quality: str = "medium") -> Optional[Dict]:
        """تحميل محسن عبر yt-dlp مع تدوير الكوكيز وإدارة الجودة"""
        if not YT_DLP_AVAILABLE:
            LOGGER(__name__).warning("yt-dlp غير متوفر")
            return None
        
        video_id = video_info.get("video_id")
        if not video_id:
            return None
        
        url = f"https://youtu.be/{video_id}"
        start_time = time.time()
        
        async with self.download_semaphore:
            self.active_downloads += 1
            LOGGER(__name__).info(f"📥 بدء التحميل: {video_id} (نشط: {self.active_downloads})")
            
            try:
                # محاولة مع الكوكيز أولاً
                if COOKIES_CYCLE:
                    for attempt in range(min(3, len(COOKIES_FILES))):
                        try:
                            cookies_file = next(COOKIES_CYCLE)
                            opts = get_ytdlp_opts(cookies_file, quality)
                            
                            loop = asyncio.get_running_loop()
                            info = await asyncio.wait_for(
                                loop.run_in_executor(
                                    self.executor_pool,
                                    lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
                                ),
                                timeout=DOWNLOAD_TIMEOUT
                            )
                            
                            if info:
                                audio_path = f"downloads/{video_id}.mp3"
                                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
                                    file_size = os.path.getsize(audio_path)
                                    
                                    if file_size > MAX_FILE_SIZE:
                                        LOGGER(__name__).warning(f"ملف كبير جداً: {file_size/1024/1024:.1f}MB")
                                        os.remove(audio_path)
                                        continue
                                    
                                    await self.update_performance_stats('ytdlp_cookies', True, time.time() - start_time)
                                    
                                    return {
                                        "audio_path": audio_path,
                                        "title": info.get("title", video_info.get("title", ""))[:80],
                                        "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                                        "duration": int(info.get("duration", video_info.get("duration", 0))),
                                        "file_size": file_size,
                                        "video_id": video_id,
                                        "source": f"ytdlp_cookies_{Path(cookies_file).name}",
                                        "quality": quality,
                                        "download_time": time.time() - start_time
                                    }
                        
                        except asyncio.TimeoutError:
                            LOGGER(__name__).warning(f"timeout في التحميل مع {cookies_file}")
                            continue
                        except Exception as e:
                            LOGGER(__name__).warning(f"فشل yt-dlp مع كوكيز {cookies_file}: {e}")
                            continue
                
                # محاولة بدون كوكيز (مع جودة أقل)
                try:
                    LOGGER(__name__).info("محاولة التحميل بدون كوكيز...")
                    fallback_quality = "low" if quality == "medium" else quality
                    opts = get_ytdlp_opts(None, fallback_quality)
                    
                    loop = asyncio.get_running_loop()
                    info = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor_pool,
                            lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True)
                        ),
                        timeout=DOWNLOAD_TIMEOUT // 2
                    )
                    
                    if info:
                        audio_path = f"downloads/{video_id}.mp3"
                        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
                            file_size = os.path.getsize(audio_path)
                            await self.update_performance_stats('ytdlp_no_cookies', True, time.time() - start_time)
                            
                            return {
                                "audio_path": audio_path,
                                "title": info.get("title", video_info.get("title", ""))[:80],
                                "artist": info.get("uploader", video_info.get("artist", "Unknown")),
                                "duration": int(info.get("duration", video_info.get("duration", 0))),
                                "file_size": file_size,
                                "video_id": video_id,
                                "source": "ytdlp_no_cookies",
                                "quality": fallback_quality,
                                "download_time": time.time() - start_time
                            }
                
                except Exception as e:
                    LOGGER(__name__).error(f"فشل yt-dlp بدون كوكيز: {e}")
                
                await self.update_performance_stats('ytdlp_no_cookies', False, time.time() - start_time)
            
            finally:
                self.active_downloads -= 1
        
        return None
    
    async def cache_to_channel(self, audio_info: Dict, search_query: str) -> Optional[str]:
        """حفظ محسن للملف في قناة التخزين وقاعدة البيانات"""
        if not SMART_CACHE_CHANNEL:
            return None
        
        try:
            audio_path = audio_info["audio_path"]
            title = audio_info["title"]
            artist = audio_info["artist"]
            duration = audio_info["duration"]
            file_size = audio_info["file_size"]
            video_id = audio_info.get("video_id", "")
            quality = audio_info.get("quality", "unknown")
            
            # إنشاء caption محسن للملف
            caption = f"""🎵 **{title}**
🎤 **{artist}**
⏱️ **{duration}s** | 📊 **{file_size/1024/1024:.1f}MB**
🎚️ **جودة:** {quality.upper()}
🔗 **مصدر:** {audio_info["source"]}
🔍 **بحث:** {search_query}
📅 **{datetime.now().strftime('%Y-%m-%d %H:%M')}**"""
            
            # رفع الملف للقناة مع Telethon
            try:
                with open(audio_path, 'rb') as audio_file:
                    # إنشاء DocumentAttributeAudio
                    audio_attr = DocumentAttributeAudio(
                        duration=duration,
                        title=title,
                        performer=artist
                    )
                    
                    message = await telethon_manager.bot_client.send_file(
                        entity=SMART_CACHE_CHANNEL,
                        file=audio_file,
                        caption=caption,
                        attributes=[audio_attr],
                        supports_streaming=True
                    )
                    
                    if message and message.media:
                        file_id = str(message.media.document.id)
                        file_unique_id = str(message.media.document.access_hash)
                        
                        # حفظ في قاعدة البيانات المحسنة
                        await self.save_to_database(
                            message.id, file_id, file_unique_id, title, artist, 
                            duration, video_id, file_size, search_query, audio_info
                        )
                        
                        LOGGER(__name__).info(f"✅ تم حفظ {title} في التخزين الذكي")
                        return file_id
                        
            except Exception as upload_error:
                LOGGER(__name__).error(f"فشل رفع الملف: {upload_error}")
                return None
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ التخزين: {e}")
        
        return None
    
    async def save_to_database(self, message_id: int, file_id: str, file_unique_id: str,
                             title: str, artist: str, duration: int, video_id: str,
                             file_size: int, search_query: str, audio_info: Dict):
        """حفظ محسن في قاعدة البيانات"""
        try:
            search_hash = self.create_search_hash(title, artist)
            normalized_title = self.normalize_text(title)
            normalized_artist = self.normalize_text(artist)
            keywords = self.create_keywords_vector(title, artist, search_query)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO channel_index 
                (message_id, file_id, file_unique_id, file_size, search_hash, 
                 title_normalized, artist_normalized, keywords_vector, original_title, 
                 original_artist, duration, video_id, download_source, download_quality, 
                 download_time, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                message_id, file_id, file_unique_id, file_size, search_hash,
                normalized_title, normalized_artist, keywords, title,
                artist, duration, video_id, audio_info.get("source", "unknown"),
                audio_info.get("quality", "unknown"), audio_info.get("download_time", 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            LOGGER(__name__).error(f"فشل حفظ قاعدة البيانات: {e}")
    
    async def hyper_download(self, query: str, quality: str = "medium") -> Optional[Dict]:
        """النظام الخارق المطور للتحميل مع جميع الطرق وإدارة محسنة"""
        start_time = time.time()
        
        try:
            LOGGER(__name__).info(f"🔍 بدء البحث الخارق: {query}")
            
            # خطوة 1: البحث الفوري في الكاش المحسن
            cached_result = await self.lightning_search_cache(query)
            if cached_result:
                search_time = time.time() - start_time
                LOGGER(__name__).info(f"⚡ كاش فوري: {query} ({search_time:.3f}s)")
                return cached_result
            
            # خطوة 2: البحث عن معلومات الفيديو بالتوازي المحسن
            search_tasks = []
            
            # إضافة المهام بناء على الأداء والتوفر
            if API_KEYS_CYCLE and self.method_performance['youtube_api']['active']:
                search_tasks.append(('youtube_api', self.youtube_api_search(query)))
            
            if INVIDIOUS_CYCLE and self.method_performance['invidious']['active']:
                search_tasks.append(('invidious', self.invidious_search(query)))
            
            if YOUTUBE_SEARCH_AVAILABLE and self.method_performance['youtube_search']['active']:
                search_tasks.append(('youtube_search', self.youtube_search_simple(query)))
            
            if not search_tasks:
                LOGGER(__name__).error("لا توجد طرق بحث متاحة")
                return None
            
            # تشغيل جميع عمليات البحث بالتوازي مع timeout
            try:
                search_results = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in search_tasks], return_exceptions=True),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                LOGGER(__name__).warning("timeout في عمليات البحث")
                return None
            
            # اختيار أفضل نتيجة بناء على الأداء
            video_info = None
            for i, result in enumerate(search_results):
                if isinstance(result, dict) and result.get("video_id"):
                    method_name = search_tasks[i][0]
                    result['search_method'] = method_name
                    video_info = result
                    break
            
            if not video_info:
                LOGGER(__name__).warning(f"لم يتم العثور على نتائج للبحث: {query}")
                return None
            
            LOGGER(__name__).info(f"🎵 تم العثور على: {video_info['title']} عبر {video_info.get('search_method', 'unknown')}")
            
            # خطوة 3: تحميل الصوت المحسن
            audio_info = await self.download_with_ytdlp(video_info, quality)
            if not audio_info:
                LOGGER(__name__).error(f"فشل التحميل: {video_info['title']}")
                return None
            
            # خطوة 4: حفظ في التخزين الذكي (في الخلفية)
            if SMART_CACHE_CHANNEL:
                asyncio.create_task(self.cache_to_channel(audio_info, query))
            
            total_time = time.time() - start_time
            LOGGER(__name__).info(f"✅ تحميل جديد مكتمل: {query} ({total_time:.3f}s)")
            
            return {
                'audio_path': audio_info['audio_path'],
                'title': audio_info['title'],
                'artist': audio_info['artist'],
                'duration': audio_info['duration'],
                'file_size': audio_info['file_size'],
                'video_id': audio_info.get('video_id'),
                'source': audio_info['source'],
                'quality': audio_info.get('quality', quality),
                'search_method': video_info.get('search_method'),
                'total_time': total_time,
                'cached': False
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في التحميل الخارق: {e}")
            return None
    
    async def cleanup_old_files(self):
        """تنظيف الملفات القديمة"""
        try:
            downloads_dir = Path("downloads")
            if downloads_dir.exists():
                now = time.time()
                for file_path in downloads_dir.iterdir():
                    if file_path.is_file() and now - file_path.stat().st_mtime > 3600:  # ساعة واحدة
                        try:
                            file_path.unlink()
                        except:
                            pass
        except Exception as e:
            LOGGER(__name__).warning(f"فشل تنظيف الملفات: {e}")

# إنشاء مدير التحميل العالمي المطور
downloader = EnhancedHyperSpeedDownloader()

# --- وظائف مساعدة محسنة ---
async def remove_temp_files(*paths):
    """حذف الملفات المؤقتة مع معالجة أخطاء محسنة"""
    for path in paths:
        if path and os.path.exists(path):
            try:
                await asyncio.sleep(0.1)  # انتظار قصير للتأكد من انتهاء العمليات
                os.remove(path)
                LOGGER(__name__).debug(f"تم حذف: {path}")
            except Exception as e:
                LOGGER(__name__).warning(f"فشل حذف {path}: {e}")

async def download_thumbnail(url: str, title: str) -> Optional[str]:
    """تحميل محسن للصورة المصغرة"""
    if not url:
        return None
    
    try:
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
        thumb_path = f"downloads/thumb_{title_clean[:20]}_{int(time.time())}.jpg"
        
        session = await downloader.get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                content = await resp.read()
                if len(content) > 1024:  # التأكد من أن الصورة ليست فارغة
                    async with aiofiles.open(thumb_path, mode='wb') as f:
                        await f.write(content)
                    return thumb_path
    except Exception as e:
        LOGGER(__name__).warning(f"فشل تحميل الصورة: {e}")
    
    return None

def format_file_size(size_bytes: int) -> str:
    """تنسيق حجم الملف"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"

def format_duration(seconds: int) -> str:
    """تنسيق المدة الزمنية"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}:{seconds%60:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"

LOGGER(__name__).info("🚀 تم تحميل نظام التحميل الذكي المطور الخارق")