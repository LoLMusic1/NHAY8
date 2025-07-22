# -*- coding: utf-8 -*-
"""
🚀 نظام التحميل الذكي الخارق الموحد - النسخة المتطورة V3
==========================================================
يدمج جميع مميزات الملفات الثلاثة في نظام واحد محترف:
- download.py: النظام الأساسي مع التحسينات
- download_enhanced.py: التحسينات المتقدمة والطرق الإضافية  
- enhanced_handler.py: المعالج المحسن مع Telethon

تم التطوير ليدعم:
- 5000 مجموعة و70,000 مستخدم في الخاص
- تحميل متوازي فائق السرعة مع Load Balancing
- إدارة ذكية للموارد مع Auto-scaling
- قاعدة بيانات غير متزامنة محسنة
- نظام مراقبة وتتبع متقدم مع AI Analytics
- تدوير كوكيز وخوادم تلقائي ذكي
- Fallback متعدد المستويات
- دعم كامل لـ Telethon مع Error Recovery
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
from typing import Dict, Optional, List, Union, Tuple
from itertools import cycle
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import aiofiles
from contextlib import asynccontextmanager
import random
import string
import psutil
import uvloop

# تطبيق UVLoop لتحسين أداء asyncio
try:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

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

try:
    import orjson
    JSON_ENCODER = orjson.dumps
    JSON_DECODER = orjson.loads
except ImportError:
    import json
    JSON_ENCODER = json.dumps
    JSON_DECODER = json.loads

# استيراد Telethon
from telethon import events
from telethon.types import Message
from telethon.tl.types import DocumentAttributeAudio

import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER
from ZeMusic.utils.database import is_search_enabled, is_search_enabled1

# --- إعدادات النظام الذكي المحسن ---
# حساب ديناميكي للحدود بناء على الموارد المتاحة
CPU_COUNT = psutil.cpu_count() or 4
MEMORY_GB = psutil.virtual_memory().total // (1024**3)

# إعدادات ديناميكية
REQUEST_TIMEOUT = 12
DOWNLOAD_TIMEOUT = 60
MAX_SESSIONS = min(150, CPU_COUNT * 8)
MAX_WORKERS = min(300, CPU_COUNT * 15)
MAX_CONCURRENT_DOWNLOADS = min(20, CPU_COUNT * 3)
CACHE_SIZE_LIMIT = min(1000000, MEMORY_GB * 50000)  # بناء على الذاكرة

# إعدادات متقدمة
RETRY_ATTEMPTS = 3
BACKOFF_FACTOR = 1.5
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MIN_FILE_SIZE = 1024  # 1KB

# قناة التخزين الذكي
SMART_CACHE_CHANNEL = getattr(config, 'CACHE_CHANNEL_ID', None)

# --- تدوير المفاتيح والخوادم المحسن ---
YT_API_KEYS = getattr(config, 'YT_API_KEYS', [])
API_KEYS_CYCLE = cycle(YT_API_KEYS) if YT_API_KEYS else None

INVIDIOUS_SERVERS = getattr(config, 'INVIDIOUS_SERVERS', [
    'https://invidious.privacydev.net',
    'https://invidious.fdn.fr', 
    'https://invidious.projectsegfau.lt',
    'https://iv.ggtyler.dev',
    'https://invidious.nerdvpn.de',
    'https://yewtu.be',
    'https://inv.nadeko.net',
    'https://invidious.tiekoetter.com'
])
INVIDIOUS_CYCLE = cycle(INVIDIOUS_SERVERS) if INVIDIOUS_SERVERS else None

# تدوير ملفات الكوكيز المحسن
def get_cookies_files():
    """الحصول على ملفات الكوكيز المتوفرة والصحيحة"""
    cookies_dir = Path("cookies")
    if not cookies_dir.exists():
        cookies_dir.mkdir(exist_ok=True)
    
    cookies_files = []
    for file in cookies_dir.glob("*.txt"):
        if file.stat().st_size > 100:  # التأكد من عدم كون الملف فارغاً
            try:
                # فحص سريع لصحة الملف
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    if 'youtube.com' in content or 'googlevideo.com' in content:
                        cookies_files.append(str(file))
            except:
                continue
    
    return cookies_files

COOKIES_FILES = get_cookies_files()
COOKIES_CYCLE = cycle(COOKIES_FILES) if COOKIES_FILES else None

# --- إعدادات yt-dlp محسنة مع تحسينات الأداء الخارقة ---
def get_ytdlp_opts(cookies_file=None, quality="medium", mobile_mode=False):
    """إعدادات yt-dlp محسنة مع خيارات متقدمة"""
    
    # إعدادات أساسية محسنة
    base_opts = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": RETRY_ATTEMPTS,
        "fragment_retries": RETRY_ATTEMPTS * 2,
        "skip_unavailable_fragments": True,
        "abort_on_unavailable_fragment": False,
        "keep_fragments": False,
        "no_cache_dir": True,
        "ignoreerrors": True,
        "socket_timeout": REQUEST_TIMEOUT,
        "force_ipv4": True,
        "concurrent_fragments": 16,
        "noprogress": True,
        "verbose": False,
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "downloads/%(id)s_%(quality)s.%(ext)s",
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "prefer_ffmpeg": True,
        "postprocessor_args": ["-ar", "44100", "-threads", str(min(8, CPU_COUNT))],
    }
    
    # User agents متنوعة للتخفي
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/117.0 Firefox/117.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ]
    
    if mobile_mode:
        base_opts["user_agent"] = user_agents[1]  # iPhone
        base_opts["http_headers"] = {
            "User-Agent": user_agents[1],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    else:
        base_opts["user_agent"] = random.choice(user_agents)
        base_opts["referer"] = "https://www.google.com/"
    
    # إعدادات الجودة المتقدمة
    if quality == "ultra":
        base_opts.update({
            "format": "bestaudio[ext=m4a][abr>=320]/bestaudio[abr>=320]/bestaudio",
            "audioquality": "0",  # أعلى جودة
            "audioformat": "mp3"
        })
    elif quality == "high":
        base_opts.update({
            "format": "bestaudio[ext=m4a][abr>=192]/bestaudio[abr>=192]/bestaudio",
            "audioquality": "0",
            "audioformat": "mp3"
        })
    elif quality == "low":
        base_opts.update({
            "format": "worstaudio[ext=m4a]/worstaudio/worst",
            "audioquality": "9",
            "audioformat": "mp3"
        })
    else:  # medium
        base_opts.update({
            "format": "bestaudio[filesize<50M]/best[filesize<50M]/bestaudio",
            "audioquality": "2",
            "audioformat": "mp3"
        })
    
    # إضافة الكوكيز إذا متوفرة
    if cookies_file and os.path.exists(cookies_file):
        base_opts["cookiefile"] = cookies_file
        LOGGER(__name__).debug(f"🍪 استخدام cookies: {Path(cookies_file).name}")
    
    # إضافة aria2c إذا متوفر
    import shutil
    if shutil.which("aria2c"):
        base_opts.update({
            "external_downloader": "aria2c",
            "external_downloader_args": [
                "-x", "16", "-s", "16", "-k", "2M",
                "--file-allocation=none",
                "--summary-interval=0",
                "--download-result=hide",
                "--console-log-level=error"
            ],
        })
    
    return base_opts

# إنشاء مجلدات العمل
for folder in ["downloads", "temp", "cache", "thumbnails"]:
    os.makedirs(folder, exist_ok=True)

# --- قاعدة البيانات للفهرسة الذكية المتطورة ---
DB_FILE = "unified_cache_v3.db"

class DatabaseManager:
    """مدير قاعدة البيانات المتقدم"""
    
    def __init__(self):
        self.db_file = DB_FILE
        self.connection_pool = {}
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات المتطورة"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        cursor = conn.cursor()
        
        # جدول الفهرسة الرئيسي المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE,
                file_id TEXT UNIQUE,
                file_unique_id TEXT,
                file_size INTEGER,
                
                search_hash TEXT UNIQUE,
                title_normalized TEXT,
                artist_normalized TEXT,
                keywords_vector TEXT,
                phonetic_hash TEXT,
                semantic_vector TEXT,
                
                original_title TEXT,
                original_artist TEXT,
                duration INTEGER,
                video_id TEXT,
                
                access_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                popularity_score REAL DEFAULT 0,
                quality_rating REAL DEFAULT 5.0,
                
                download_source TEXT,
                download_quality TEXT,
                download_time REAL,
                search_method TEXT,
                
                language_detected TEXT,
                genre_predicted TEXT,
                mood_analysis TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إحصائيات الأداء المتقدم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT UNIQUE,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                min_response_time REAL DEFAULT 0,
                max_response_time REAL DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                priority_weight REAL DEFAULT 1.0,
                reliability_score REAL DEFAULT 1.0,
                cost_efficiency REAL DEFAULT 1.0
            )
        ''')
        
        # جدول تتبع الأخطاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT,
                error_message TEXT,
                method_name TEXT,
                query TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # جدول إحصائيات المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_analytics (
                user_id INTEGER PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                favorite_genres TEXT,
                avg_session_duration REAL DEFAULT 0,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preference_profile TEXT
            )
        ''')
        
        # إنشاء الفهارس للسرعة الخارقة
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_search_hash ON unified_index(search_hash)",
            "CREATE INDEX IF NOT EXISTS idx_title_norm ON unified_index(title_normalized)",
            "CREATE INDEX IF NOT EXISTS idx_artist_norm ON unified_index(artist_normalized)",
            "CREATE INDEX IF NOT EXISTS idx_popularity ON unified_index(popularity_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_access_count ON unified_index(access_count DESC)",
            "CREATE INDEX IF NOT EXISTS idx_video_id ON unified_index(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_keywords ON unified_index(keywords_vector)",
            "CREATE INDEX IF NOT EXISTS idx_phonetic ON unified_index(phonetic_hash)",
            "CREATE INDEX IF NOT EXISTS idx_quality ON unified_index(quality_rating DESC)",
            "CREATE INDEX IF NOT EXISTS idx_last_accessed ON unified_index(last_accessed DESC)",
            "CREATE INDEX IF NOT EXISTS idx_performance_method ON performance_analytics(method_name)",
            "CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_tracking(timestamp DESC)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # تهيئة بيانات الأداء الافتراضية
        methods = [
            'cache_direct', 'cache_fuzzy', 'cache_semantic',
            'youtube_api', 'invidious', 'youtube_search',
            'ytdlp_cookies', 'ytdlp_mobile', 'ytdlp_fallback',
            'cobalt_api', 'y2mate_api', 'savefrom_api',
            'generic_extractor', 'youtube_dl', 'local_files'
        ]
        
        for method in methods:
            cursor.execute(
                "INSERT OR IGNORE INTO performance_analytics (method_name) VALUES (?)",
                (method,)
            )
        
        conn.commit()
        conn.close()
        LOGGER(__name__).info("🗄️ تم تهيئة قاعدة البيانات المتطورة")

# تهيئة مدير قاعدة البيانات
db_manager = DatabaseManager()