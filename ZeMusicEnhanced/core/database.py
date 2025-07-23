#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🗄️ Database Manager - ZeMusic Bot v3.0
تاريخ الإنشاء: 2025-01-28

مدير قاعدة البيانات المتقدم مع دعم SQLite و MongoDB
"""

import sqlite3
import json
import asyncio
import threading
import time
import logging
from typing import Dict, List, Union, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)

@dataclass
class ChatSettings:
    """إعدادات المجموعة"""
    chat_id: int
    language: str = "ar"
    play_mode: str = "Direct"
    play_type: str = "Everyone"
    assistant_id: Optional[int] = None
    auto_end: bool = False
    auth_enabled: bool = False
    welcome_enabled: bool = False
    log_enabled: bool = False
    search_enabled: bool = True
    upvote_count: int = 3
    loop_mode: int = 0
    skip_mode: str = "Admin"
    allow_nonadmin: bool = False
    connected_channel: Optional[int] = None
    force_channels: List[int] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class UserData:
    """بيانات المستخدم"""
    user_id: int
    first_name: str = ""
    username: Optional[str] = None
    join_date: str = field(default_factory=lambda: datetime.now().isoformat())
    is_banned: bool = False
    is_sudo: bool = False
    language: str = "ar"
    total_plays: int = 0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ChatData:
    """بيانات المجموعة"""
    chat_id: int
    chat_title: str = ""
    chat_type: str = ""
    join_date: str = field(default_factory=lambda: datetime.now().isoformat())
    is_blacklisted: bool = False
    member_count: int = 0
    total_plays: int = 0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AssistantData:
    """بيانات الحساب المساعد"""
    assistant_id: int
    session_string: str
    name: str
    phone: Optional[str] = None
    is_active: bool = True
    added_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    total_calls: int = 0
    total_errors: int = 0

@dataclass
class PlayHistory:
    """تاريخ التشغيل"""
    id: Optional[int] = None
    chat_id: int = 0
    user_id: int = 0
    song_title: str = ""
    song_url: str = ""
    duration: int = 0
    platform: str = ""
    played_at: str = field(default_factory=lambda: datetime.now().isoformat())

class DatabaseManager:
    """مدير قاعدة البيانات المتقدم"""
    
    def __init__(self, db_path: str = None):
        """تهيئة مدير قاعدة البيانات"""
        if db_path:
            self.db_path = db_path
        elif hasattr(config, 'DATABASE_PATH') and config.DATABASE_PATH:
            self.db_path = config.DATABASE_PATH
        else:
            self.db_path = 'zemusic_enhanced.db'
        self._lock = threading.Lock()
        self._connection_pool = {}
        
        # كاش في الذاكرة للبيانات المتكررة
        self.cache_enabled = getattr(config, 'ENABLE_DATABASE_CACHE', True)
        self.cache_ttl = getattr(config, 'DATABASE_CACHE_TTL', 3600)
        
        if self.cache_enabled:
            self.cache = {
                'settings': {},
                'users': {},
                'chats': {},
                'assistants': {},
                'temp': {},
                'timestamps': {}
            }
        else:
            self.cache = {}
        
        # إحصائيات قاعدة البيانات
        self.stats = {
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors_count': 0,
            'last_backup': None,
            'total_users': 0,
            'total_chats': 0,
            'total_assistants': 0
        }
        
    async def initialize(self) -> bool:
        """تهيئة قاعدة البيانات"""
        try:
            logger.info("🗄️ تهيئة قاعدة البيانات...")
            
            # إنشاء مجلد قاعدة البيانات
            import os
            if os.path.dirname(self.db_path):
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # إنشاء الجداول
            await self._create_tables()
            
            # بدء مهام الصيانة
            asyncio.create_task(self._cleanup_cache())
            asyncio.create_task(self._backup_scheduler())
            asyncio.create_task(self._statistics_updater())
            
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة قاعدة البيانات: {e}")
            return False
    
    @contextmanager
    def _get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    async def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول إعدادات المجموعات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_settings (
                    chat_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ar',
                    play_mode TEXT DEFAULT 'Direct',
                    play_type TEXT DEFAULT 'Everyone',
                    assistant_id INTEGER DEFAULT NULL,
                    auto_end BOOLEAN DEFAULT 0,
                    auth_enabled BOOLEAN DEFAULT 0,
                    welcome_enabled BOOLEAN DEFAULT 0,
                    log_enabled BOOLEAN DEFAULT 0,
                    search_enabled BOOLEAN DEFAULT 1,
                    upvote_count INTEGER DEFAULT 3,
                    loop_mode INTEGER DEFAULT 0,
                    skip_mode TEXT DEFAULT 'Admin',
                    allow_nonadmin BOOLEAN DEFAULT 0,
                    connected_channel INTEGER DEFAULT NULL,
                    force_channels TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول بيانات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT DEFAULT '',
                    username TEXT DEFAULT NULL,
                    join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT 0,
                    is_sudo BOOLEAN DEFAULT 0,
                    language TEXT DEFAULT 'ar',
                    total_plays INTEGER DEFAULT 0,
                    last_activity TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول بيانات المجموعات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT DEFAULT '',
                    chat_type TEXT DEFAULT '',
                    join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_blacklisted BOOLEAN DEFAULT 0,
                    member_count INTEGER DEFAULT 0,
                    total_plays INTEGER DEFAULT 0,
                    last_activity TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول الحسابات المساعدة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assistants (
                    assistant_id INTEGER PRIMARY KEY,
                    session_string TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT DEFAULT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    total_calls INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0
                )
            ''')
            
            # جدول تاريخ التشغيل
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    song_title TEXT NOT NULL,
                    song_url TEXT DEFAULT '',
                    duration INTEGER DEFAULT 0,
                    platform TEXT DEFAULT '',
                    played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول المستخدمين المصرح لهم
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_users (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    added_by INTEGER NOT NULL,
                    added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول الحالات المؤقتة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_states (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TEXT DEFAULT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء فهارس للأداء
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_play_history_chat ON play_history(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_play_history_user ON play_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_play_history_date ON play_history(played_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_users_chat ON auth_users(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chats_activity ON chats(last_activity)')
            
            conn.commit()
            self.stats['queries_executed'] += 8
    
    # ==================== إدارة إعدادات المجموعات ====================
    
    async def get_chat_settings(self, chat_id: int) -> ChatSettings:
        """الحصول على إعدادات المجموعة"""
        try:
            # التحقق من الكاش
            cache_key = f"settings_{chat_id}"
            if self.cache_enabled and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.cache['settings'][chat_id]
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM chat_settings WHERE chat_id = ?',
                    (chat_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    settings = ChatSettings(
                        chat_id=row['chat_id'],
                        language=row['language'],
                        play_mode=row['play_mode'],
                        play_type=row['play_type'],
                        assistant_id=row['assistant_id'],
                        auto_end=bool(row['auto_end']),
                        auth_enabled=bool(row['auth_enabled']),
                        welcome_enabled=bool(row['welcome_enabled']),
                        log_enabled=bool(row['log_enabled']),
                        search_enabled=bool(row['search_enabled']),
                        upvote_count=row['upvote_count'],
                        loop_mode=row['loop_mode'],
                        skip_mode=row['skip_mode'],
                        allow_nonadmin=bool(row['allow_nonadmin']),
                        connected_channel=row['connected_channel'],
                        force_channels=json.loads(row['force_channels']),
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                else:
                    # إنشاء إعدادات افتراضية
                    settings = ChatSettings(chat_id=chat_id)
                    await self._insert_default_chat_settings(chat_id)
                
                # حفظ في الكاش
                if self.cache_enabled:
                    self.cache['settings'][chat_id] = settings
                    self.cache['timestamps'][cache_key] = time.time()
                    self.stats['cache_misses'] += 1
                
                self.stats['queries_executed'] += 1
                return settings
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب إعدادات المجموعة {chat_id}: {e}")
            self.stats['errors_count'] += 1
            return ChatSettings(chat_id=chat_id)
    
    async def update_chat_setting(self, chat_id: int, **kwargs) -> bool:
        """تحديث إعدادات المجموعة"""
        try:
            if not kwargs:
                return True
            
            # إضافة وقت التحديث
            kwargs['updated_at'] = datetime.now().isoformat()
            
            # بناء استعلام التحديث
            set_clause = ', '.join(f"{key} = ?" for key in kwargs.keys())
            values = list(kwargs.values()) + [chat_id]
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'UPDATE chat_settings SET {set_clause} WHERE chat_id = ?',
                    values
                )
                
                if cursor.rowcount == 0:
                    # إنشاء إعدادات جديدة إذا لم تكن موجودة
                    await self._insert_default_chat_settings(chat_id)
                    cursor.execute(
                        f'UPDATE chat_settings SET {set_clause} WHERE chat_id = ?',
                        values
                    )
                
                conn.commit()
            
            # تحديث الكاش
            if self.cache_enabled and chat_id in self.cache['settings']:
                settings = self.cache['settings'][chat_id]
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
            
            self.stats['queries_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إعدادات المجموعة {chat_id}: {e}")
            self.stats['errors_count'] += 1
            return False
    
    async def _insert_default_chat_settings(self, chat_id: int):
        """إدراج إعدادات افتراضية للمجموعة"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO chat_settings (chat_id) VALUES (?)',
                (chat_id,)
            )
            conn.commit()
    
    # ==================== إدارة المستخدمين ====================
    
    async def add_served_user(self, user_id: int, first_name: str = "", username: str = None) -> bool:
        """إضافة مستخدم للخدمة"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO users 
                       (user_id, first_name, username, last_activity) 
                       VALUES (?, ?, ?, ?)''',
                    (user_id, first_name, username, datetime.now().isoformat())
                )
                conn.commit()
            
            self.stats['queries_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المستخدم {user_id}: {e}")
            self.stats['errors_count'] += 1
            return False
    
    async def get_user_data(self, user_id: int) -> Optional[UserData]:
        """الحصول على بيانات المستخدم"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return UserData(
                        user_id=row['user_id'],
                        first_name=row['first_name'],
                        username=row['username'],
                        join_date=row['join_date'],
                        is_banned=bool(row['is_banned']),
                        is_sudo=bool(row['is_sudo']),
                        language=row['language'],
                        total_plays=row['total_plays'],
                        last_activity=row['last_activity']
                    )
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب بيانات المستخدم {user_id}: {e}")
            return None
    
    async def ban_user(self, user_id: int) -> bool:
        """حظر مستخدم"""
        return await self._update_user_field(user_id, 'is_banned', True)
    
    async def unban_user(self, user_id: int) -> bool:
        """إلغاء حظر مستخدم"""
        return await self._update_user_field(user_id, 'is_banned', False)
    
    async def is_banned_user(self, user_id: int) -> bool:
        """التحقق من حظر المستخدم"""
        try:
            user_data = await self.get_user_data(user_id)
            return user_data.is_banned if user_data else False
        except Exception:
            return False
    
    # ==================== إدارة المجموعات ====================
    
    async def add_served_chat(self, chat_id: int, chat_title: str = "", chat_type: str = "") -> bool:
        """إضافة مجموعة للخدمة"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO chats 
                       (chat_id, chat_title, chat_type, last_activity) 
                       VALUES (?, ?, ?, ?)''',
                    (chat_id, chat_title, chat_type, datetime.now().isoformat())
                )
                conn.commit()
            
            self.stats['queries_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المجموعة {chat_id}: {e}")
            self.stats['errors_count'] += 1
            return False
    
    async def blacklist_chat(self, chat_id: int) -> bool:
        """إضافة مجموعة للقائمة السوداء"""
        return await self._update_chat_field(chat_id, 'is_blacklisted', True)
    
    async def whitelist_chat(self, chat_id: int) -> bool:
        """إزالة مجموعة من القائمة السوداء"""
        return await self._update_chat_field(chat_id, 'is_blacklisted', False)
    
    async def is_blacklisted_chat(self, chat_id: int) -> bool:
        """التحقق من وجود المجموعة في القائمة السوداء"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT is_blacklisted FROM chats WHERE chat_id = ?',
                    (chat_id,)
                )
                row = cursor.fetchone()
                return bool(row['is_blacklisted']) if row else False
        except Exception:
            return False
    
    # ==================== إدارة الحسابات المساعدة ====================
    
    async def add_assistant(self, assistant_data: AssistantData) -> bool:
        """إضافة حساب مساعد"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO assistants 
                       (assistant_id, session_string, name, phone, is_active) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (assistant_data.assistant_id, assistant_data.session_string,
                     assistant_data.name, assistant_data.phone, assistant_data.is_active)
                )
                conn.commit()
            
            self.stats['queries_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المساعد {assistant_data.assistant_id}: {e}")
            self.stats['errors_count'] += 1
            return False
    
    async def get_all_assistants(self) -> List[AssistantData]:
        """الحصول على جميع الحسابات المساعدة"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assistants WHERE is_active = 1')
                rows = cursor.fetchall()
                
                return [
                    AssistantData(
                        assistant_id=row['assistant_id'],
                        session_string=row['session_string'],
                        name=row['name'],
                        phone=row['phone'],
                        is_active=bool(row['is_active']),
                        added_date=row['added_date'],
                        last_used=row['last_used'],
                        total_calls=row['total_calls'],
                        total_errors=row['total_errors']
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الحسابات المساعدة: {e}")
            return []
    
    # ==================== تاريخ التشغيل ====================
    
    async def add_play_history(self, history: PlayHistory) -> bool:
        """إضافة سجل تشغيل"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO play_history 
                       (chat_id, user_id, song_title, song_url, duration, platform) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (history.chat_id, history.user_id, history.song_title,
                     history.song_url, history.duration, history.platform)
                )
                conn.commit()
            
            # تحديث إحصائيات المستخدم والمجموعة
            await self._update_user_field(history.user_id, 'total_plays', 
                                        f'total_plays + 1', is_expression=True)
            await self._update_chat_field(history.chat_id, 'total_plays', 
                                        f'total_plays + 1', is_expression=True)
            
            self.stats['queries_executed'] += 3
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة سجل التشغيل: {e}")
            self.stats['errors_count'] += 1
            return False
    
    # ==================== الحالات المؤقتة ====================
    
    async def set_temp_state(self, key: str, value: Any, expires_in: int = None) -> bool:
        """تعيين حالة مؤقتة"""
        try:
            expires_at = None
            if expires_in:
                expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO temp_states (key, value, expires_at) 
                       VALUES (?, ?, ?)''',
                    (key, json.dumps(value), expires_at)
                )
                conn.commit()
            
            self.stats['queries_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تعيين الحالة المؤقتة {key}: {e}")
            return False
    
    async def get_temp_state(self, key: str, default: Any = None) -> Any:
        """الحصول على حالة مؤقتة"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT value, expires_at FROM temp_states WHERE key = ?',
                    (key,)
                )
                row = cursor.fetchone()
                
                if row:
                    # التحقق من انتهاء الصلاحية
                    if row['expires_at']:
                        expires_at = datetime.fromisoformat(row['expires_at'])
                        if datetime.now() > expires_at:
                            await self.delete_temp_state(key)
                            return default
                    
                    return json.loads(row['value'])
                
                return default
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الحالة المؤقتة {key}: {e}")
            return default
    
    async def delete_temp_state(self, key: str) -> bool:
        """حذف حالة مؤقتة"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM temp_states WHERE key = ?', (key,))
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف الحالة المؤقتة {key}: {e}")
            return False
    
    # ==================== وظائف مساعدة ====================
    
    async def _update_user_field(self, user_id: int, field: str, value: Any, is_expression: bool = False) -> bool:
        """تحديث حقل في جدول المستخدمين"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if is_expression:
                    cursor.execute(
                        f'UPDATE users SET {field} = {value}, last_activity = ? WHERE user_id = ?',
                        (datetime.now().isoformat(), user_id)
                    )
                else:
                    cursor.execute(
                        f'UPDATE users SET {field} = ?, last_activity = ? WHERE user_id = ?',
                        (value, datetime.now().isoformat(), user_id)
                    )
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث حقل المستخدم {field}: {e}")
            return False
    
    async def _update_chat_field(self, chat_id: int, field: str, value: Any, is_expression: bool = False) -> bool:
        """تحديث حقل في جدول المجموعات"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if is_expression:
                    cursor.execute(
                        f'UPDATE chats SET {field} = {value}, last_activity = ? WHERE chat_id = ?',
                        (datetime.now().isoformat(), chat_id)
                    )
                else:
                    cursor.execute(
                        f'UPDATE chats SET {field} = ?, last_activity = ? WHERE chat_id = ?',
                        (value, datetime.now().isoformat(), chat_id)
                    )
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث حقل المجموعة {field}: {e}")
            return False
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """التحقق من صحة الكاش"""
        if not self.cache_enabled or cache_key not in self.cache['timestamps']:
            return False
        
        timestamp = self.cache['timestamps'][cache_key]
        return time.time() - timestamp < self.cache_ttl
    
    # ==================== مهام الصيانة ====================
    
    async def _cleanup_cache(self):
        """تنظيف الكاش المنتهي الصلاحية"""
        while True:
            try:
                await asyncio.sleep(300)  # كل 5 دقائق
                
                if not self.cache_enabled:
                    continue
                
                current_time = time.time()
                expired_keys = []
                
                for key, timestamp in self.cache['timestamps'].items():
                    if current_time - timestamp > self.cache_ttl:
                        expired_keys.append(key)
                
                # إزالة الكاش المنتهي الصلاحية
                for key in expired_keys:
                    cache_type = key.split('_')[0]
                    if cache_type in self.cache:
                        item_id = int(key.split('_')[1])
                        if item_id in self.cache[cache_type]:
                            del self.cache[cache_type][item_id]
                    del self.cache['timestamps'][key]
                
                if expired_keys:
                    logger.info(f"🧹 تم تنظيف {len(expired_keys)} عنصر من الكاش")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تنظيف الكاش: {e}")
    
    async def _backup_scheduler(self):
        """جدولة النسخ الاحتياطية"""
        while True:
            try:
                await asyncio.sleep(86400)  # كل 24 ساعة
                await self.create_backup()
                
            except Exception as e:
                logger.error(f"❌ خطأ في جدولة النسخ الاحتياطي: {e}")
    
    async def _statistics_updater(self):
        """تحديث الإحصائيات"""
        while True:
            try:
                await asyncio.sleep(3600)  # كل ساعة
                
                # تنظيف الحالات المؤقتة المنتهية الصلاحية
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'DELETE FROM temp_states WHERE expires_at IS NOT NULL AND expires_at < ?',
                        (datetime.now().isoformat(),)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"🗑️ تم حذف {deleted_count} حالة مؤقتة منتهية الصلاحية")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    # ==================== إدارة النسخ الاحتياطية ====================
    
    async def create_backup(self) -> bool:
        """إنشاء نسخة احتياطية"""
        try:
            import shutil
            backup_path = f"{self.db_path}.backup.{int(time.time())}"
            shutil.copy2(self.db_path, backup_path)
            
            self.stats['last_backup'] = datetime.now().isoformat()
            logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء النسخة الاحتياطية: {e}")
            return False
    
    # ==================== الإحصائيات ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات قاعدة البيانات"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # إحصائيات المستخدمين
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 0')
                active_users = cursor.fetchone()[0]
                
                # إحصائيات المجموعات
                cursor.execute('SELECT COUNT(*) FROM chats')
                total_chats = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM chats WHERE is_blacklisted = 0')
                active_chats = cursor.fetchone()[0]
                
                # إحصائيات التشغيل
                cursor.execute('SELECT COUNT(*) FROM play_history')
                total_plays = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM play_history WHERE played_at >= datetime("now", "-1 day")')
                plays_today = cursor.fetchone()[0]
                
                # إحصائيات الحسابات المساعدة
                cursor.execute('SELECT COUNT(*) FROM assistants WHERE is_active = 1')
                active_assistants = cursor.fetchone()[0]
                
                return {
                    'database': {
                        **self.stats,
                        'cache_enabled': self.cache_enabled,
                        'cache_size': len(self.cache.get('timestamps', {}))
                    },
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'banned': total_users - active_users
                    },
                    'chats': {
                        'total': total_chats,
                        'active': active_chats,
                        'blacklisted': total_chats - active_chats
                    },
                    'plays': {
                        'total': total_plays,
                        'today': plays_today
                    },
                    'assistants': {
                        'active': active_assistants
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الإحصائيات: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """فحص صحة قاعدة البيانات"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل فحص صحة قاعدة البيانات: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات قاعدة البيانات"""
        try:
            # تحديث الإحصائيات
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # عدد المستخدمين
                cursor.execute("SELECT COUNT(*) FROM users")
                self.stats['total_users'] = cursor.fetchone()[0]
                
                # عدد المجموعات
                cursor.execute("SELECT COUNT(*) FROM chats")
                self.stats['total_chats'] = cursor.fetchone()[0]
                
                # عدد الحسابات المساعدة
                cursor.execute("SELECT COUNT(*) FROM assistants")
                self.stats['total_assistants'] = cursor.fetchone()[0]
                
            return self.stats.copy()
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب إحصائيات قاعدة البيانات: {e}")
            return self.stats.copy()
    
    def close(self):
        """إغلاق قاعدة البيانات"""
        try:
            # إيقاف مهام الصيانة
            if hasattr(self, 'cleanup_task') and self.cleanup_task:
                self.cleanup_task.cancel()
            if hasattr(self, 'backup_task') and self.backup_task:
                self.backup_task.cancel()
            if hasattr(self, 'stats_task') and self.stats_task:
                self.stats_task.cancel()
                
            # مسح الكاش
            if self.cache_enabled:
                self.cache.clear()
                
            # إغلاق الاتصالات
            for conn in self._connection_pool.values():
                if conn:
                    conn.close()
            self._connection_pool.clear()
            
            logger.info("✅ تم إغلاق قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إغلاق قاعدة البيانات: {e}")
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """إضافة مستخدم جديد"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, created_at, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, datetime.now(), datetime.now()))
                conn.commit()
                
            logger.debug(f"✅ تم إضافة المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المستخدم {user_id}: {e}")
            return False

# إنشاء مثيل عام لمدير قاعدة البيانات
db = DatabaseManager()