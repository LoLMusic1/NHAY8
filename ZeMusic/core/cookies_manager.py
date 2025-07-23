# -*- coding: utf-8 -*-
"""
مدير ملفات Cookies الذكي
نظام متطور لإدارة ملفات cookies مع التدوير والكشف عن المحظورة
"""

import os
import json
import time
import random
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from itertools import cycle
import aiofiles

from ZeMusic.zemusic_logging import LOGGER

class CookiesManager:
    """مدير ملفات cookies ذكي مع نظام تدوير وإدارة الحظر"""
    
    def __init__(self, cookies_dir: str = "cookies"):
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(exist_ok=True)
        
        # ملف لحفظ حالة الcookies
        self.status_file = self.cookies_dir / "cookies_status.json"
        
        # إعدادات افتراضية
        self.max_failures = 3  # عدد المحاولات قبل تعطيل cookie
        self.retry_timeout = 3600  # وقت انتظار قبل إعادة تجربة cookie محظور (ساعة)
        self.rotation_delay = 2  # تأخير بين التبديل (ثانية)
        
        # حالة الcookies
        self.cookies_status: Dict[str, Dict] = {}
        self.available_cookies: List[str] = []
        self.current_index = 0
        
        # إحصائيات
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cookies_blocked': 0,
            'cookies_recovered': 0
        }
        
        LOGGER(__name__).info("🍪 تم تهيئة مدير Cookies الذكي")
    
    async def initialize(self):
        """تهيئة المدير وتحميل حالة الcookies"""
        await self._load_cookies_status()
        await self._scan_cookies_files()
        await self._update_available_cookies()
        
        LOGGER(__name__).info(f"📋 تم العثور على {len(self.available_cookies)} ملف cookies صالح")
    
    async def _load_cookies_status(self):
        """تحميل حالة الcookies من الملف"""
        try:
            if self.status_file.exists():
                async with aiofiles.open(self.status_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.cookies_status = data.get('cookies_status', {})
                    self.usage_stats = data.get('usage_stats', self.usage_stats)
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ فشل تحميل حالة cookies: {e}")
            self.cookies_status = {}
    
    async def _save_cookies_status(self):
        """حفظ حالة الcookies في الملف"""
        try:
            data = {
                'cookies_status': self.cookies_status,
                'usage_stats': self.usage_stats,
                'last_updated': int(time.time())
            }
            
            async with aiofiles.open(self.status_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            LOGGER(__name__).error(f"❌ فشل حفظ حالة cookies: {e}")
    
    async def _scan_cookies_files(self):
        """فحص ملفات cookies في المجلد مع دعم الإضافة والحذف الديناميكي"""
        current_files = set()
        new_files = []
        
        # فحص جميع ملفات .txt في المجلد
        for file_path in self.cookies_dir.glob("*.txt"):
            if file_path.name.startswith('.'):
                continue
                
            try:
                # التحقق من أن الملف ليس فارغاً
                if file_path.stat().st_size == 0:
                    LOGGER(__name__).warning(f"🗑️ ملف cookies فارغ: {file_path.name}")
                    continue
                
                cookie_path = str(file_path)
                current_files.add(cookie_path)
                
                # إنشاء حالة افتراضية إذا لم تكن موجودة (ملف جديد)
                if cookie_path not in self.cookies_status:
                    self.cookies_status[cookie_path] = {
                        'active': True,
                        'failures': 0,
                        'last_used': 0,
                        'last_failure': 0,
                        'success_count': 0,
                        'total_requests': 0,
                        'blocked_until': 0,
                        'added_at': int(time.time())
                    }
                    new_files.append(file_path.name)
                    LOGGER(__name__).info(f"🆕 تم اكتشاف ملف cookies جديد: {file_path.name}")
                    
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ خطأ في فحص {file_path}: {e}")
        
        # إزالة ملفات محذوفة من القائمة
        removed_files = []
        for cookie_path in list(self.cookies_status.keys()):
            if cookie_path not in current_files:
                removed_files.append(Path(cookie_path).name)
                del self.cookies_status[cookie_path]
                LOGGER(__name__).info(f"🗑️ تم حذف ملف cookies من النظام: {Path(cookie_path).name}")
        
        # تقرير التغييرات
        if new_files:
            LOGGER(__name__).info(f"📁 تم إضافة {len(new_files)} ملف cookies جديد: {', '.join(new_files)}")
        
        if removed_files:
            LOGGER(__name__).info(f"🗑️ تم إزالة {len(removed_files)} ملف cookies: {', '.join(removed_files)}")
        
        return {'added': new_files, 'removed': removed_files}
    
    async def _update_available_cookies(self):
        """تحديث قائمة الcookies المتاحة"""
        current_time = int(time.time())
        self.available_cookies = []
        
        for cookie_path, status in self.cookies_status.items():
            # التحقق من وجود الملف
            if not os.path.exists(cookie_path):
                continue
            
            # التحقق من عدم الحظر
            if status.get('blocked_until', 0) > current_time:
                continue
            
            # التحقق من أن الcookie نشط
            if not status.get('active', True):
                continue
            
            self.available_cookies.append(cookie_path)
        
        # ترتيب عشوائي لتوزيع الحمولة
        random.shuffle(self.available_cookies)
        
        LOGGER(__name__).debug(f"🔄 تحديث قائمة cookies: {len(self.available_cookies)} متاح")
    
    async def get_next_cookie(self) -> Optional[str]:
        """الحصول على ملف cookie التالي"""
        if not self.available_cookies:
            await self._update_available_cookies()
            
        if not self.available_cookies:
            LOGGER(__name__).warning("⚠️ لا توجد ملفات cookies متاحة")
            return None
        
        # التدوير مع تأخير خفيف
        if len(self.available_cookies) > 1:
            await asyncio.sleep(self.rotation_delay)
        
        # اختيار التالي في الدورة
        cookie_path = self.available_cookies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.available_cookies)
        
        # تحديث وقت الاستخدام
        if cookie_path in self.cookies_status:
            self.cookies_status[cookie_path]['last_used'] = int(time.time())
            self.cookies_status[cookie_path]['total_requests'] += 1
        
        self.usage_stats['total_requests'] += 1
        
        LOGGER(__name__).debug(f"🍪 استخدام cookie: {Path(cookie_path).name}")
        return cookie_path
    
    async def report_success(self, cookie_path: str):
        """تسجيل نجاح استخدام cookie"""
        if cookie_path in self.cookies_status:
            status = self.cookies_status[cookie_path]
            status['success_count'] += 1
            status['failures'] = 0  # إعادة تعيين عداد الفشل
            
            self.usage_stats['successful_requests'] += 1
            
            # إذا كان محظوراً وعمل الآن، أعده للقائمة
            if status.get('blocked_until', 0) > int(time.time()):
                status['blocked_until'] = 0
                status['active'] = True
                await self._update_available_cookies()
                self.usage_stats['cookies_recovered'] += 1
                LOGGER(__name__).info(f"✅ تم استرداد cookie: {Path(cookie_path).name}")
        
        await self._save_cookies_status()
    
    async def report_failure(self, cookie_path: str, error_message: str = ""):
        """تسجيل فشل استخدام cookie"""
        if cookie_path not in self.cookies_status:
            return
        
        status = self.cookies_status[cookie_path]
        status['failures'] += 1
        status['last_failure'] = int(time.time())
        
        self.usage_stats['failed_requests'] += 1
        
        # التحقق من نوع الخطأ
        is_blocked = any(keyword in error_message.lower() for keyword in [
            '403', '401', 'forbidden', 'unauthorized', 'blocked', 'banned',
            'rate limit', 'too many requests', 'quota exceeded'
        ])
        
        # إذا فشل كثيراً أو محظور، قم بتعطيله مؤقتاً
        if status['failures'] >= self.max_failures or is_blocked:
            status['blocked_until'] = int(time.time()) + self.retry_timeout
            status['active'] = False
            await self._update_available_cookies()
            
            self.usage_stats['cookies_blocked'] += 1
            
            LOGGER(__name__).warning(
                f"🚫 تم حظر cookie مؤقتاً: {Path(cookie_path).name} "
                f"(فشل {status['failures']} مرات)"
            )
        else:
            LOGGER(__name__).debug(
                f"⚠️ فشل cookie: {Path(cookie_path).name} "
                f"({status['failures']}/{self.max_failures})"
            )
        
        await self._save_cookies_status()
    
    async def remove_invalid_cookie(self, cookie_path: str, reason: str = "غير صالح"):
        """إزالة cookie غير صالح نهائياً"""
        try:
            if os.path.exists(cookie_path):
                # نقل إلى مجلد احتياطي بدلاً من الحذف
                backup_dir = self.cookies_dir / "invalid"
                backup_dir.mkdir(exist_ok=True)
                
                backup_path = backup_dir / f"{Path(cookie_path).stem}_{int(time.time())}.txt"
                os.rename(cookie_path, backup_path)
                
                LOGGER(__name__).info(f"🗑️ تم نقل cookie غير صالح: {Path(cookie_path).name} - {reason}")
            
            # إزالة من القوائم
            if cookie_path in self.cookies_status:
                del self.cookies_status[cookie_path]
            
            if cookie_path in self.available_cookies:
                self.available_cookies.remove(cookie_path)
            
            await self._save_cookies_status()
            
        except Exception as e:
            LOGGER(__name__).error(f"❌ فشل إزالة cookie: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الاستخدام"""
        await self._update_available_cookies()
        
        # إحصائيات عامة
        total_cookies = len(self.cookies_status)
        active_cookies = len(self.available_cookies)
        blocked_cookies = total_cookies - active_cookies
        
        # معدل النجاح
        success_rate = 0
        if self.usage_stats['total_requests'] > 0:
            success_rate = (self.usage_stats['successful_requests'] / 
                          self.usage_stats['total_requests']) * 100
        
        return {
            'total_cookies': total_cookies,
            'active_cookies': active_cookies,
            'blocked_cookies': blocked_cookies,
            'success_rate': round(success_rate, 2),
            'usage_stats': self.usage_stats.copy(),
            'cookies_details': [
                {
                    'file': Path(path).name,
                    'active': status.get('active', True),
                    'failures': status.get('failures', 0),
                    'success_count': status.get('success_count', 0),
                    'total_requests': status.get('total_requests', 0),
                    'blocked_until': status.get('blocked_until', 0)
                }
                for path, status in self.cookies_status.items()
                if os.path.exists(path)
            ]
        }
    
    async def reset_cookie(self, cookie_path: str):
        """إعادة تعيين حالة cookie محدد"""
        if cookie_path in self.cookies_status:
            self.cookies_status[cookie_path].update({
                'active': True,
                'failures': 0,
                'blocked_until': 0
            })
            await self._update_available_cookies()
            await self._save_cookies_status()
            
            LOGGER(__name__).info(f"🔄 تم إعادة تعيين cookie: {Path(cookie_path).name}")
    
    async def reset_all_cookies(self):
        """إعادة تعيين جميع cookies"""
        for cookie_path in self.cookies_status:
            await self.reset_cookie(cookie_path)
        
        LOGGER(__name__).info("🔄 تم إعادة تعيين جميع cookies")

# إنشاء مثيل global
cookies_manager = CookiesManager()

# دوال مساعدة للتوافق مع الكود الحالي
async def get_random_cookie() -> Optional[str]:
    """الحصول على cookie عشوائي (للتوافق مع الكود القديم)"""
    return await cookies_manager.get_next_cookie()

async def report_cookie_success(cookie_path: str):
    """تسجيل نجاح cookie"""
    await cookies_manager.report_success(cookie_path)

async def report_cookie_failure(cookie_path: str, error: str = ""):
    """تسجيل فشل cookie"""
    await cookies_manager.report_failure(cookie_path, error)