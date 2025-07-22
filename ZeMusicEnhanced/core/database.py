#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Database Manager
تاريخ الإنشاء: 2025-01-28

نظام إدارة قاعدة بيانات محسن مع دعم SQLite و PostgreSQL
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import aiosqlite

try:
    import asyncpg
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..config import config

logger = logging.getLogger(__name__)

# ============================================
# نماذج البيانات
# ============================================

@dataclass
class UserData:
    """نموذج بيانات المستخدم"""
    user_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    language: str = "ar"
    is_banned: bool = False
    is_sudo: bool = False
    join_date: datetime = None
    last_activity: datetime = None
    total_plays: int = 0
    
    def __post_init__(self):
        if self.join_date is None:
            self.join_date = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

@dataclass
class ChatData:
    """نموذج بيانات المحادثة"""
    chat_id: int
    chat_type: str = "group"
    title: str = ""
    username: str = ""
    language: str = "ar"
    is_banned: bool = False
    join_date: datetime = None
    last_activity: datetime = None
    total_plays: int = 0
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.join_date is None:
            self.join_date = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.settings is None:
            self.settings = {}

@dataclass
class AssistantData:
    """نموذج بيانات الحساب المساعد"""
    assistant_id: int
    session_string: str
    name: str = ""
    username: str = ""
    phone: str = ""
    is_active: bool = True
    is_connected: bool = False
    created_date: datetime = None
    last_used: datetime = None
    total_calls: int = 0
    active_calls: int = 0
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()

@dataclass
class PlayHistory:
    """نموذج سجل التشغيل"""
    id: int = None
    chat_id: int = 0
    user_id: int = 0
    title: str = ""
    url: str = ""
    duration: int = 0
    platform: str = "youtube"
    played_at: datetime = None
    
    def __post_init__(self):
        if self.played_at is None:
            self.played_at = datetime.now()

# ============================================
# مدير قاعدة البيانات
# ============================================

class DatabaseManager:
    """مدير قاعدة البيانات المحسن"""
    
    def __init__(self):
        """تهيئة مدير قاعدة البيانات"""
        self.db_url = config.database.database_url
        self.is_sqlite = config.database.is_sqlite
        self.is_postgresql = config.database.is_postgresql
        
        # اتصال قاعدة البيانات
        self.connection = None
        self.connection_pool = None
        
        # ذاكرة التخزين المؤقت
        self.cache_enabled = config.database.enable_cache
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        
        # Redis للتخزين المؤقت المتقدم
        self.redis_client = None
        if config.performance.enable_redis and REDIS_AVAILABLE:
            self.redis_enabled = True
        else:
            self.redis_enabled = False
    
    async def initialize(self) -> bool:
        """تهيئة قاعدة البيانات"""
        try:
            logger.info("🗃️ تهيئة قاعدة البيانات...")
            
            # إنشاء مجلد قاعدة البيانات للـ SQLite
            if self.is_sqlite:
                db_path = Path(self.db_url.replace("sqlite:///", ""))
                db_path.parent.mkdir(exist_ok=True)
            
            # الاتصال بقاعدة البيانات
            if not await self._connect():
                return False
            
            # إنشاء الجداول
            await self._create_tables()
            
            # تهيئة Redis إذا كان مفعلاً
            if self.redis_enabled:
                await self._init_redis()
            
            # بدء مهام الصيانة
            asyncio.create_task(self._maintenance_tasks())
            
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة قاعدة البيانات: {e}")
            return False
    
    async def _connect(self) -> bool:
        """الاتصال بقاعدة البيانات"""
        try:
            if self.is_sqlite:
                # SQLite
                self.connection = await aiosqlite.connect(
                    self.db_url.replace("sqlite:///", "")
                )
                await self.connection.execute("PRAGMA foreign_keys = ON")
                await self.connection.execute("PRAGMA journal_mode = WAL")
                
            elif self.is_postgresql and POSTGRESQL_AVAILABLE:
                # PostgreSQL
                self.connection_pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=1,
                    max_size=config.database.connection_pool_size
                )
                
            else:
                logger.error("❌ نوع قاعدة البيانات غير مدعوم")
                return False
            
            logger.info(f"✅ تم الاتصال بقاعدة البيانات ({self._get_db_type()})")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في الاتصال بقاعدة البيانات: {e}")
            return False
    
    async def _init_redis(self):
        """تهيئة Redis للتخزين المؤقت"""
        try:
            self.redis_client = redis.from_url(
                config.performance.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ تم الاتصال بـ Redis")
            
        except Exception as e:
            logger.warning(f"⚠️ فشل في الاتصال بـ Redis: {e}")
            self.redis_enabled = False
    
    async def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        
        # جدول المستخدمين
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            language TEXT DEFAULT 'ar',
            is_banned BOOLEAN DEFAULT FALSE,
            is_sudo BOOLEAN DEFAULT FALSE,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_plays INTEGER DEFAULT 0
        )
        """
        
        # جدول المحادثات
        chats_table = """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_type TEXT DEFAULT 'group',
            title TEXT DEFAULT '',
            username TEXT DEFAULT '',
            language TEXT DEFAULT 'ar',
            is_banned BOOLEAN DEFAULT FALSE,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_plays INTEGER DEFAULT 0,
            settings TEXT DEFAULT '{}'
        )
        """
        
        # جدول الحسابات المساعدة
        assistants_table = """
        CREATE TABLE IF NOT EXISTS assistants (
            assistant_id INTEGER PRIMARY KEY,
            session_string TEXT NOT NULL,
            name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE,
            is_connected BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            total_calls INTEGER DEFAULT 0,
            active_calls INTEGER DEFAULT 0
        )
        """
        
        # جدول سجل التشغيل
        play_history_table = """
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            title TEXT DEFAULT '',
            url TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            platform TEXT DEFAULT 'youtube',
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # جدول الإحصائيات
        stats_table = """
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT '0',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        tables = [
            users_table, chats_table, assistants_table,
            play_history_table, stats_table
        ]
        
        try:
            for table_sql in tables:
                await self._execute(table_sql)
            
            # إنشاء فهارس للأداء
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_chats_title ON chats(title)",
                "CREATE INDEX IF NOT EXISTS idx_assistants_active ON assistants(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_play_history_chat ON play_history(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_play_history_date ON play_history(played_at)"
            ]
            
            for index_sql in indexes:
                await self._execute(index_sql)
            
            logger.info("✅ تم إنشاء جداول قاعدة البيانات")
            
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء الجداول: {e}")
            raise
    
    async def _execute(self, query: str, params: tuple = None) -> Any:
        """تنفيذ استعلام قاعدة البيانات"""
        try:
            if self.is_sqlite:
                if params:
                    cursor = await self.connection.execute(query, params)
                else:
                    cursor = await self.connection.execute(query)
                await self.connection.commit()
                return cursor
                
            elif self.is_postgresql:
                async with self.connection_pool.acquire() as conn:
                    if params:
                        return await conn.execute(query, *params)
                    else:
                        return await conn.execute(query)
                        
        except Exception as e:
            logger.error(f"❌ فشل في تنفيذ الاستعلام: {e}")
            raise
    
    async def _fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """جلب سجل واحد"""
        try:
            if self.is_sqlite:
                self.connection.row_factory = aiosqlite.Row
                if params:
                    cursor = await self.connection.execute(query, params)
                else:
                    cursor = await self.connection.execute(query)
                row = await cursor.fetchone()
                return dict(row) if row else None
                
            elif self.is_postgresql:
                async with self.connection_pool.acquire() as conn:
                    if params:
                        row = await conn.fetchrow(query, *params)
                    else:
                        row = await conn.fetchrow(query)
                    return dict(row) if row else None
                    
        except Exception as e:
            logger.error(f"❌ فشل في جلب السجل: {e}")
            return None
    
    async def _fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """جلب جميع السجلات"""
        try:
            if self.is_sqlite:
                self.connection.row_factory = aiosqlite.Row
                if params:
                    cursor = await self.connection.execute(query, params)
                else:
                    cursor = await self.connection.execute(query)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
            elif self.is_postgresql:
                async with self.connection_pool.acquire() as conn:
                    if params:
                        rows = await conn.fetch(query, *params)
                    else:
                        rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"❌ فشل في جلب السجلات: {e}")
            return []
    
    # ============================================
    # وظائف المستخدمين
    # ============================================
    
    async def add_user(self, user_data: UserData) -> bool:
        """إضافة مستخدم جديد"""
        try:
            query = """
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, language, is_banned, is_sudo, join_date, last_activity, total_plays)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user_data.user_id, user_data.username, user_data.first_name,
                user_data.last_name, user_data.language, user_data.is_banned,
                user_data.is_sudo, user_data.join_date, user_data.last_activity,
                user_data.total_plays
            )
            
            await self._execute(query, params)
            
            # تحديث الكاش
            if self.cache_enabled:
                self._set_cache(f"user:{user_data.user_id}", user_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في إضافة المستخدم {user_data.user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[UserData]:
        """الحصول على بيانات المستخدم"""
        try:
            # البحث في الكاش أولاً
            if self.cache_enabled:
                cached = self._get_cache(f"user:{user_id}")
                if cached:
                    return cached
            
            query = "SELECT * FROM users WHERE user_id = ?"
            row = await self._fetch_one(query, (user_id,))
            
            if row:
                user_data = UserData(**row)
                
                # حفظ في الكاش
                if self.cache_enabled:
                    self._set_cache(f"user:{user_id}", user_data)
                
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب بيانات المستخدم {user_id}: {e}")
            return None
    
    async def update_user_activity(self, user_id: int) -> bool:
        """تحديث نشاط المستخدم"""
        try:
            query = "UPDATE users SET last_activity = ? WHERE user_id = ?"
            await self._execute(query, (datetime.now(), user_id))
            
            # تحديث الكاش
            if self.cache_enabled:
                self._invalidate_cache(f"user:{user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تحديث نشاط المستخدم {user_id}: {e}")
            return False
    
    # ============================================
    # وظائف المحادثات
    # ============================================
    
    async def add_chat(self, chat_data: ChatData) -> bool:
        """إضافة محادثة جديدة"""
        try:
            query = """
            INSERT OR REPLACE INTO chats 
            (chat_id, chat_type, title, username, language, is_banned, join_date, last_activity, total_plays, settings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                chat_data.chat_id, chat_data.chat_type, chat_data.title,
                chat_data.username, chat_data.language, chat_data.is_banned,
                chat_data.join_date, chat_data.last_activity, chat_data.total_plays,
                json.dumps(chat_data.settings)
            )
            
            await self._execute(query, params)
            
            # تحديث الكاش
            if self.cache_enabled:
                self._set_cache(f"chat:{chat_data.chat_id}", chat_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في إضافة المحادثة {chat_data.chat_id}: {e}")
            return False
    
    async def get_chat(self, chat_id: int) -> Optional[ChatData]:
        """الحصول على بيانات المحادثة"""
        try:
            # البحث في الكاش أولاً
            if self.cache_enabled:
                cached = self._get_cache(f"chat:{chat_id}")
                if cached:
                    return cached
            
            query = "SELECT * FROM chats WHERE chat_id = ?"
            row = await self._fetch_one(query, (chat_id,))
            
            if row:
                # تحويل settings من JSON
                if row['settings']:
                    row['settings'] = json.loads(row['settings'])
                else:
                    row['settings'] = {}
                
                chat_data = ChatData(**row)
                
                # حفظ في الكاش
                if self.cache_enabled:
                    self._set_cache(f"chat:{chat_id}", chat_data)
                
                return chat_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب بيانات المحادثة {chat_id}: {e}")
            return None
    
    # ============================================
    # وظائف الحسابات المساعدة
    # ============================================
    
    async def add_assistant(self, assistant_data: AssistantData) -> bool:
        """إضافة حساب مساعد"""
        try:
            query = """
            INSERT OR REPLACE INTO assistants 
            (assistant_id, session_string, name, username, phone, is_active, is_connected, created_date, last_used, total_calls, active_calls)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                assistant_data.assistant_id, assistant_data.session_string,
                assistant_data.name, assistant_data.username, assistant_data.phone,
                assistant_data.is_active, assistant_data.is_connected,
                assistant_data.created_date, assistant_data.last_used,
                assistant_data.total_calls, assistant_data.active_calls
            )
            
            await self._execute(query, params)
            
            # تحديث الكاش
            if self.cache_enabled:
                self._invalidate_cache("assistants:all")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في إضافة الحساب المساعد {assistant_data.assistant_id}: {e}")
            return False
    
    async def get_all_assistants(self) -> List[AssistantData]:
        """الحصول على جميع الحسابات المساعدة"""
        try:
            # البحث في الكاش أولاً
            if self.cache_enabled:
                cached = self._get_cache("assistants:all")
                if cached:
                    return cached
            
            query = "SELECT * FROM assistants WHERE is_active = TRUE ORDER BY assistant_id"
            rows = await self._fetch_all(query)
            
            assistants = [AssistantData(**row) for row in rows]
            
            # حفظ في الكاش
            if self.cache_enabled:
                self._set_cache("assistants:all", assistants, ttl_minutes=5)
            
            return assistants
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب الحسابات المساعدة: {e}")
            return []
    
    async def update_assistant_status(self, assistant_id: int, is_connected: bool, active_calls: int = None) -> bool:
        """تحديث حالة الحساب المساعد"""
        try:
            if active_calls is not None:
                query = "UPDATE assistants SET is_connected = ?, active_calls = ?, last_used = ? WHERE assistant_id = ?"
                params = (is_connected, active_calls, datetime.now(), assistant_id)
            else:
                query = "UPDATE assistants SET is_connected = ?, last_used = ? WHERE assistant_id = ?"
                params = (is_connected, datetime.now(), assistant_id)
            
            await self._execute(query, params)
            
            # تحديث الكاش
            if self.cache_enabled:
                self._invalidate_cache("assistants:all")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تحديث حالة الحساب المساعد {assistant_id}: {e}")
            return False
    
    # ============================================
    # وظائف الإحصائيات
    # ============================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات البوت"""
        try:
            stats = {}
            
            # إحصائيات المستخدمين
            users_count = await self._fetch_one("SELECT COUNT(*) as count FROM users")
            stats['users'] = users_count['count'] if users_count else 0
            
            # إحصائيات المحادثات
            chats_count = await self._fetch_one("SELECT COUNT(*) as count FROM chats")
            stats['chats'] = chats_count['count'] if chats_count else 0
            
            # إحصائيات الحسابات المساعدة
            assistants_count = await self._fetch_one("SELECT COUNT(*) as count FROM assistants WHERE is_active = TRUE")
            stats['assistants'] = assistants_count['count'] if assistants_count else 0
            
            # الحسابات المتصلة
            connected_assistants = await self._fetch_one("SELECT COUNT(*) as count FROM assistants WHERE is_connected = TRUE")
            stats['connected_assistants'] = connected_assistants['count'] if connected_assistants else 0
            
            # إجمالي التشغيلات
            total_plays = await self._fetch_one("SELECT COUNT(*) as count FROM play_history")
            stats['total_plays'] = total_plays['count'] if total_plays else 0
            
            # التشغيلات اليوم
            today_plays = await self._fetch_one(
                "SELECT COUNT(*) as count FROM play_history WHERE DATE(played_at) = DATE('now')"
            )
            stats['plays_today'] = today_plays['count'] if today_plays else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب الإحصائيات: {e}")
            return {}
    
    # ============================================
    # وظائف التخزين المؤقت
    # ============================================
    
    def _set_cache(self, key: str, value: Any, ttl_minutes: int = 15):
        """حفظ في الكاش"""
        if not self.cache_enabled:
            return
        
        self.cache[key] = value
        self.cache_ttl[key] = datetime.now() + timedelta(minutes=ttl_minutes)
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """جلب من الكاش"""
        if not self.cache_enabled:
            return None
        
        if key in self.cache:
            # فحص انتهاء الصلاحية
            if key in self.cache_ttl and datetime.now() > self.cache_ttl[key]:
                self._invalidate_cache(key)
                return None
            
            return self.cache[key]
        
        return None
    
    def _invalidate_cache(self, key: str):
        """إلغاء الكاش"""
        if key in self.cache:
            del self.cache[key]
        if key in self.cache_ttl:
            del self.cache_ttl[key]
    
    def _clear_cache(self):
        """مسح جميع الكاش"""
        self.cache.clear()
        self.cache_ttl.clear()
    
    # ============================================
    # مهام الصيانة
    # ============================================
    
    async def _maintenance_tasks(self):
        """مهام الصيانة الدورية"""
        while True:
            try:
                await asyncio.sleep(3600)  # كل ساعة
                
                # تنظيف الكاش المنتهي الصلاحية
                await self._cleanup_expired_cache()
                
                # النسخ الاحتياطي التلقائي
                if config.database.auto_backup:
                    await self._create_backup()
                
            except Exception as e:
                logger.error(f"❌ خطأ في مهام الصيانة: {e}")
    
    async def _cleanup_expired_cache(self):
        """تنظيف الكاش المنتهي الصلاحية"""
        if not self.cache_enabled:
            return
        
        now = datetime.now()
        expired_keys = [
            key for key, expire_time in self.cache_ttl.items()
            if now > expire_time
        ]
        
        for key in expired_keys:
            self._invalidate_cache(key)
        
        if expired_keys:
            logger.info(f"🧹 تم تنظيف {len(expired_keys)} عنصر من الكاش")
    
    async def _create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            if self.is_sqlite:
                import shutil
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"zemusic_backup_{timestamp}.db"
                
                db_file = Path(self.db_url.replace("sqlite:///", ""))
                shutil.copy2(db_file, backup_file)
                
                logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_file}")
                
                # حذف النسخ القديمة
                await self._cleanup_old_backups()
                
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء النسخة الاحتياطية: {e}")
    
    async def _cleanup_old_backups(self):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            backup_dir = Path("backups")
            if not backup_dir.exists():
                return
            
            backups = list(backup_dir.glob("zemusic_backup_*.db"))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # الاحتفاظ بآخر N نسخة
            keep_count = config.database.backup_keep_count
            if len(backups) > keep_count:
                for backup in backups[keep_count:]:
                    backup.unlink()
                    logger.info(f"🗑️ تم حذف النسخة الاحتياطية القديمة: {backup}")
                    
        except Exception as e:
            logger.error(f"❌ فشل في تنظيف النسخ الاحتياطية: {e}")
    
    def _get_db_type(self) -> str:
        """الحصول على نوع قاعدة البيانات"""
        if self.is_sqlite:
            return "SQLite"
        elif self.is_postgresql:
            return "PostgreSQL"
        else:
            return "Unknown"
    
    async def close(self):
        """إغلاق الاتصالات"""
        try:
            if self.connection:
                await self.connection.close()
                
            if self.connection_pool:
                await self.connection_pool.close()
                
            if self.redis_client:
                await self.redis_client.close()
                
            logger.info("✅ تم إغلاق اتصالات قاعدة البيانات")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إغلاق قاعدة البيانات: {e}")

# إنشاء مثيل عام لمدير قاعدة البيانات
db = DatabaseManager()