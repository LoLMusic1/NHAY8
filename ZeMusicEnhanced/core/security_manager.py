#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Security Manager
تاريخ الإنشاء: 2025-01-28

نظام الأمان المحسن مع حماية شاملة من التهديدات
"""

import asyncio
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict, deque
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from .database import db

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """حدث أمني"""
    user_id: int
    chat_id: int
    event_type: str
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    
@dataclass
class UserRateLimit:
    """حد المعدل للمستخدم"""
    user_id: int
    message_count: int
    first_message_time: datetime
    last_message_time: datetime
    is_banned: bool = False
    ban_expiry: Optional[datetime] = None

class SecurityManager:
    """مدير الأمان المحسن"""
    
    def __init__(self, client, database):
        """تهيئة مدير الأمان"""
        self.client = client
        self.database = database
        
        # حماية من السبام
        self.user_rate_limits: Dict[int, UserRateLimit] = {}
        self.chat_rate_limits: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # حماية من الفلود
        self.flood_protection_data: Dict[int, List[float]] = defaultdict(list)
        
        # المستخدمون المحظورون مؤقتاً
        self.temp_banned_users: Dict[int, datetime] = {}
        
        # المحادثات المحظورة مؤقتاً
        self.temp_banned_chats: Dict[int, datetime] = {}
        
        # كشف الأنماط المشبوهة
        self.suspicious_patterns: Dict[str, int] = {}
        self.user_behavior: Dict[int, Dict[str, Any]] = defaultdict(dict)
        
        # سجل الأحداث الأمنية
        self.security_events: List[SecurityEvent] = []
        
        # مهام الصيانة
        self.cleanup_task = None
        self.monitoring_task = None
        
    async def initialize(self) -> bool:
        """تهيئة نظام الأمان"""
        try:
            logger.info("🛡️ تهيئة نظام الأمان...")
            
            # تحميل قوائم الحظر من قاعدة البيانات
            await self._load_security_data()
            
            # بدء مهام المراقبة
            self._start_monitoring_tasks()
            
            logger.info("✅ تم تهيئة نظام الأمان بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة نظام الأمان: {e}")
            return False
    
    async def _load_security_data(self):
        """تحميل بيانات الأمان من قاعدة البيانات"""
        try:
            # تحميل المستخدمين المحظورين
            # سيتم تنفيذ هذا عند إضافة وظائف قاعدة البيانات المناسبة
            
            logger.info("📚 تم تحميل بيانات الأمان")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل بيانات الأمان: {e}")
    
    def _start_monitoring_tasks(self):
        """بدء مهام المراقبة الأمنية"""
        # تنظيف البيانات القديمة
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data())
        
        # مراقبة الأنشطة المشبوهة
        self.monitoring_task = asyncio.create_task(self._monitor_suspicious_activity())
        
        logger.info("👁️ تم بدء مهام المراقبة الأمنية")
    
    async def check_user_permission(self, user_id: int, chat_id: int, action: str) -> Dict[str, Any]:
        """فحص صلاحيات المستخدم"""
        try:
            # فحص الحظر العام
            if await self.is_user_banned(user_id):
                return {
                    'allowed': False,
                    'reason': 'user_banned',
                    'message': 'المستخدم محظور من استخدام البوت'
                }
            
            # فحص الحظر المؤقت
            if user_id in self.temp_banned_users:
                ban_expiry = self.temp_banned_users[user_id]
                if datetime.now() < ban_expiry:
                    remaining = ban_expiry - datetime.now()
                    return {
                        'allowed': False,
                        'reason': 'temp_banned',
                        'message': f'المستخدم محظور مؤقتاً لمدة {remaining.seconds // 60} دقيقة'
                    }
                else:
                    # انتهت مدة الحظر
                    del self.temp_banned_users[user_id]
            
            # فحص حدود المعدل
            if not await self._check_rate_limit(user_id, chat_id):
                return {
                    'allowed': False,
                    'reason': 'rate_limit',
                    'message': 'تم تجاوز حد الرسائل المسموح'
                }
            
            # فحص حماية الفلود
            if not await self._check_flood_protection(user_id, chat_id):
                return {
                    'allowed': False,
                    'reason': 'flood_protection',
                    'message': 'تم اكتشاف محاولة فلود'
                }
            
            # فحص صلاحيات خاصة بالإجراء
            if not await self._check_action_permission(user_id, chat_id, action):
                return {
                    'allowed': False,
                    'reason': 'insufficient_permissions',
                    'message': 'صلاحيات غير كافية لهذا الإجراء'
                }
            
            return {
                'allowed': True,
                'reason': 'permitted'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص صلاحيات المستخدم {user_id}: {e}")
            return {
                'allowed': False,
                'reason': 'error',
                'message': 'خطأ في فحص الصلاحيات'
            }
    
    async def _check_rate_limit(self, user_id: int, chat_id: int) -> bool:
        """فحص حدود المعدل"""
        try:
            if not config.security.anti_spam:
                return True
            
            current_time = datetime.now()
            
            if user_id not in self.user_rate_limits:
                self.user_rate_limits[user_id] = UserRateLimit(
                    user_id=user_id,
                    message_count=1,
                    first_message_time=current_time,
                    last_message_time=current_time
                )
                return True
            
            rate_limit = self.user_rate_limits[user_id]
            
            # إعادة تعيين العداد كل دقيقة
            if (current_time - rate_limit.first_message_time).seconds >= 60:
                rate_limit.message_count = 1
                rate_limit.first_message_time = current_time
                rate_limit.last_message_time = current_time
                return True
            
            # زيادة العداد
            rate_limit.message_count += 1
            rate_limit.last_message_time = current_time
            
            # فحص تجاوز الحد
            if rate_limit.message_count > config.security.spam_threshold:
                # حظر مؤقت
                ban_duration = timedelta(seconds=config.security.spam_ban_duration)
                self.temp_banned_users[user_id] = current_time + ban_duration
                
                # تسجيل حدث أمني
                await self._log_security_event(
                    user_id=user_id,
                    chat_id=chat_id,
                    event_type="spam_detected",
                    severity="medium",
                    details={
                        "message_count": rate_limit.message_count,
                        "threshold": config.security.spam_threshold,
                        "ban_duration": config.security.spam_ban_duration
                    }
                )
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص حدود المعدل: {e}")
            return True  # السماح في حالة الخطأ
    
    async def _check_flood_protection(self, user_id: int, chat_id: int) -> bool:
        """فحص حماية الفلود"""
        try:
            if not config.security.flood_protection:
                return True
            
            current_time = time.time()
            
            # تنظيف الرسائل القديمة (أكثر من دقيقة)
            self.flood_protection_data[user_id] = [
                timestamp for timestamp in self.flood_protection_data[user_id]
                if current_time - timestamp < 60
            ]
            
            # إضافة الرسالة الحالية
            self.flood_protection_data[user_id].append(current_time)
            
            # فحص تجاوز حد الفلود
            if len(self.flood_protection_data[user_id]) > config.security.flood_threshold:
                # حظر مؤقت
                ban_duration = timedelta(minutes=10)  # 10 دقائق للفلود
                self.temp_banned_users[user_id] = datetime.now() + ban_duration
                
                # تسجيل حدث أمني
                await self._log_security_event(
                    user_id=user_id,
                    chat_id=chat_id,
                    event_type="flood_detected",
                    severity="high",
                    details={
                        "message_count": len(self.flood_protection_data[user_id]),
                        "threshold": config.security.flood_threshold,
                        "ban_duration": 600  # 10 دقائق
                    }
                )
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص حماية الفلود: {e}")
            return True
    
    async def _check_action_permission(self, user_id: int, chat_id: int, action: str) -> bool:
        """فحص صلاحيات الإجراء"""
        try:
            # فحص المالك
            if config.is_owner(user_id):
                return True
            
            # فحص المطورين
            if config.is_sudo(user_id):
                # المطورون لديهم صلاحيات واسعة لكن ليس كاملة
                restricted_actions = ['shutdown', 'restart', 'add_sudo', 'remove_sudo']
                return action not in restricted_actions
            
            # فحص صلاحيات المشرفين في المحادثة
            if action in ['play', 'pause', 'skip', 'stop']:
                # أوامر التشغيل الأساسية متاحة للجميع أو المشرفين حسب إعدادات المحادثة
                return True
            
            if action in ['clear_queue', 'loop', 'shuffle']:
                # أوامر متقدمة تتطلب صلاحيات مشرف
                admin_permissions = await self.client.check_admin_permissions(chat_id, user_id)
                return admin_permissions.get('is_admin', False)
            
            # إجراءات المالك فقط
            owner_only_actions = [
                'add_assistant', 'remove_assistant', 'broadcast',
                'global_ban', 'global_unban', 'maintenance_mode'
            ]
            
            if action in owner_only_actions:
                return config.is_owner(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص صلاحيات الإجراء: {e}")
            return False
    
    async def is_user_banned(self, user_id: int) -> bool:
        """فحص ما إذا كان المستخدم محظور"""
        try:
            # فحص الحظر في الإعدادات
            if user_id in config.security.banned_users:
                return True
            
            # فحص الحظر في قاعدة البيانات
            user_data = await db.get_user(user_id)
            if user_data and user_data.is_banned:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص حظر المستخدم {user_id}: {e}")
            return False
    
    async def is_chat_banned(self, chat_id: int) -> bool:
        """فحص ما إذا كانت المحادثة محظورة"""
        try:
            # فحص الحظر في الإعدادات
            if chat_id in config.security.banned_chats:
                return True
            
            # فحص الحظر المؤقت
            if chat_id in self.temp_banned_chats:
                ban_expiry = self.temp_banned_chats[chat_id]
                if datetime.now() < ban_expiry:
                    return True
                else:
                    del self.temp_banned_chats[chat_id]
            
            # فحص الحظر في قاعدة البيانات
            chat_data = await db.get_chat(chat_id)
            if chat_data and chat_data.is_banned:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص حظر المحادثة {chat_id}: {e}")
            return False
    
    async def ban_user(self, user_id: int, reason: str = "", duration: Optional[int] = None) -> Dict[str, Any]:
        """حظر مستخدم"""
        try:
            if duration:
                # حظر مؤقت
                ban_expiry = datetime.now() + timedelta(seconds=duration)
                self.temp_banned_users[user_id] = ban_expiry
                
                message = f"تم حظر المستخدم {user_id} مؤقتاً لمدة {duration // 60} دقيقة"
            else:
                # حظر دائم - إضافة لقاعدة البيانات
                user_data = await db.get_user(user_id)
                if user_data:
                    user_data.is_banned = True
                    await db.add_user(user_data)
                
                message = f"تم حظر المستخدم {user_id} نهائياً"
            
            # تسجيل حدث أمني
            await self._log_security_event(
                user_id=user_id,
                chat_id=0,
                event_type="user_banned",
                severity="high",
                details={
                    "reason": reason,
                    "duration": duration,
                    "banned_by": "system"
                }
            )
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في حظر المستخدم {user_id}: {e}")
            return {
                'success': False,
                'message': f'خطأ في حظر المستخدم: {str(e)}'
            }
    
    async def unban_user(self, user_id: int) -> Dict[str, Any]:
        """إلغاء حظر مستخدم"""
        try:
            # إلغاء الحظر المؤقت
            if user_id in self.temp_banned_users:
                del self.temp_banned_users[user_id]
            
            # إلغاء الحظر الدائم
            user_data = await db.get_user(user_id)
            if user_data and user_data.is_banned:
                user_data.is_banned = False
                await db.add_user(user_data)
            
            # تسجيل حدث أمني
            await self._log_security_event(
                user_id=user_id,
                chat_id=0,
                event_type="user_unbanned",
                severity="medium",
                details={
                    "unbanned_by": "system"
                }
            )
            
            return {
                'success': True,
                'message': f'تم إلغاء حظر المستخدم {user_id}'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في إلغاء حظر المستخدم {user_id}: {e}")
            return {
                'success': False,
                'message': f'خطأ في إلغاء حظر المستخدم: {str(e)}'
            }
    
    async def detect_suspicious_behavior(self, user_id: int, chat_id: int, message_content: str) -> bool:
        """كشف السلوك المشبوه"""
        try:
            suspicious_score = 0
            
            # أنماط مشبوهة في النص
            suspicious_patterns = [
                r'(http|https)://[^\s]+',  # روابط
                r'@[a-zA-Z0-9_]+',         # منشن مستخدمين
                r'[0-9]{10,}',             # أرقام طويلة
                r'(.)\1{4,}',              # تكرار أحرف
            ]
            
            import re
            for pattern in suspicious_patterns:
                if re.search(pattern, message_content, re.IGNORECASE):
                    suspicious_score += 1
            
            # فحص تكرار الرسائل
            if user_id not in self.user_behavior:
                self.user_behavior[user_id] = {'recent_messages': deque(maxlen=10)}
            
            recent_messages = self.user_behavior[user_id]['recent_messages']
            recent_messages.append(message_content)
            
            # حساب التشابه
            if len(recent_messages) >= 3:
                similar_count = sum(1 for msg in recent_messages if msg == message_content)
                if similar_count >= 3:
                    suspicious_score += 2
            
            # تسجيل النشاط المشبوه
            if suspicious_score >= 2:
                await self._log_security_event(
                    user_id=user_id,
                    chat_id=chat_id,
                    event_type="suspicious_behavior",
                    severity="medium",
                    details={
                        "suspicious_score": suspicious_score,
                        "message_content": message_content[:100],  # أول 100 حرف
                        "patterns_detected": suspicious_score
                    }
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ فشل في كشف السلوك المشبوه: {e}")
            return False
    
    async def _log_security_event(self, user_id: int, chat_id: int, event_type: str, 
                                  severity: str, details: Dict[str, Any]):
        """تسجيل حدث أمني"""
        try:
            event = SecurityEvent(
                user_id=user_id,
                chat_id=chat_id,
                event_type=event_type,
                severity=severity,
                details=details,
                timestamp=datetime.now()
            )
            
            self.security_events.append(event)
            
            # الاحتفاظ بآخر 1000 حدث فقط
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            # إرسال تنبيه للمالك في الحالات الخطيرة
            if severity in ['high', 'critical']:
                await self._send_security_alert(event)
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل الحدث الأمني: {e}")
    
    async def _send_security_alert(self, event: SecurityEvent):
        """إرسال تنبيه أمني للمالك"""
        try:
            if not config.channels.log_channel_id:
                return
            
            severity_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴',
                'critical': '🚨'
            }
            
            alert_message = (
                f"{severity_emoji.get(event.severity, '⚠️')} **تنبيه أمني**\n\n"
                f"**النوع:** {event.event_type}\n"
                f"**المستخدم:** {event.user_id}\n"
                f"**المحادثة:** {event.chat_id}\n"
                f"**الخطورة:** {event.severity}\n"
                f"**الوقت:** {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"**التفاصيل:**\n"
            )
            
            for key, value in event.details.items():
                alert_message += f"• {key}: {value}\n"
            
            await self.client.send_message(
                config.channels.log_channel_id,
                alert_message
            )
            
        except Exception as e:
            logger.error(f"❌ فشل في إرسال التنبيه الأمني: {e}")
    
    async def get_security_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأمان"""
        try:
            current_time = datetime.now()
            
            # إحصائيات الأحداث الأمنية
            recent_events = [
                event for event in self.security_events
                if (current_time - event.timestamp).days < 7
            ]
            
            event_types = {}
            severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            
            for event in recent_events:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
                severity_counts[event.severity] += 1
            
            return {
                'total_events': len(self.security_events),
                'recent_events': len(recent_events),
                'temp_banned_users': len(self.temp_banned_users),
                'temp_banned_chats': len(self.temp_banned_chats),
                'active_rate_limits': len(self.user_rate_limits),
                'event_types': event_types,
                'severity_counts': severity_counts,
                'flood_protection_active': len(self.flood_protection_data)
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب إحصائيات الأمان: {e}")
            return {}
    
    async def _cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        while True:
            try:
                await asyncio.sleep(3600)  # كل ساعة
                
                current_time = datetime.now()
                
                # تنظيف حدود المعدل القديمة
                expired_rate_limits = [
                    user_id for user_id, rate_limit in self.user_rate_limits.items()
                    if (current_time - rate_limit.last_message_time).seconds > 3600
                ]
                
                for user_id in expired_rate_limits:
                    del self.user_rate_limits[user_id]
                
                # تنظيف بيانات حماية الفلود القديمة
                for user_id in list(self.flood_protection_data.keys()):
                    self.flood_protection_data[user_id] = [
                        timestamp for timestamp in self.flood_protection_data[user_id]
                        if time.time() - timestamp < 3600
                    ]
                    
                    if not self.flood_protection_data[user_id]:
                        del self.flood_protection_data[user_id]
                
                # تنظيف الأحداث الأمنية القديمة (أكثر من 30 يوم)
                cutoff_date = current_time - timedelta(days=30)
                self.security_events = [
                    event for event in self.security_events
                    if event.timestamp > cutoff_date
                ]
                
                logger.info("🧹 تم تنظيف البيانات الأمنية القديمة")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تنظيف البيانات الأمنية: {e}")
    
    async def _monitor_suspicious_activity(self):
        """مراقبة الأنشطة المشبوهة"""
        while True:
            try:
                await asyncio.sleep(300)  # كل 5 دقائق
                
                # تحليل الأنماط المشبوهة
                await self._analyze_patterns()
                
            except Exception as e:
                logger.error(f"❌ خطأ في مراقبة الأنشطة المشبوهة: {e}")
    
    async def _analyze_patterns(self):
        """تحليل الأنماط المشبوهة"""
        try:
            # تحليل الأحداث الأمنية الأخيرة
            recent_events = [
                event for event in self.security_events
                if (datetime.now() - event.timestamp).minutes < 30
            ]
            
            # كشف الهجمات المنسقة
            user_counts = {}
            for event in recent_events:
                user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
            
            # إذا كان هناك مستخدم واحد مع أحداث كثيرة
            for user_id, count in user_counts.items():
                if count >= 5:  # 5 أحداث في 30 دقيقة
                    await self.ban_user(
                        user_id, 
                        "نشاط مشبوه مكثف", 
                        duration=3600  # ساعة واحدة
                    )
            
        except Exception as e:
            logger.error(f"❌ فشل في تحليل الأنماط: {e}")
    
    async def shutdown(self):
        """إيقاف نظام الأمان"""
        try:
            logger.info("🛑 إيقاف نظام الأمان...")
            
            # إيقاف مهام المراقبة
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
            
            # حفظ البيانات المهمة في قاعدة البيانات
            # (سيتم تنفيذ هذا عند الحاجة)
            
            logger.info("✅ تم إيقاف نظام الأمان")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف نظام الأمان: {e}")

# إنشاء مثيل عام لمدير الأمان
security_manager = None  # سيتم تهيئته في الملف الرئيسي