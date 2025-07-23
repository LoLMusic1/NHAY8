#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Database Utils
تاريخ الإنشاء: 2025-01-28

أدوات قاعدة البيانات والحالات المؤقتة
"""

import asyncio
from typing import Dict, List, Union, Optional, Any
from ..core.database import db

# متغيرات الذاكرة للحالات المؤقتة (كما في الكود الأصلي)
active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}

# وظائف السجلات (Logs)
async def is_loge_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل السجلات"""
    try:
        settings = await db.get_chat_settings(chat_id)
        return getattr(settings, 'log_enabled', False)
    except Exception:
        return False

async def enable_loge(chat_id: int) -> bool:
    """تفعيل السجلات"""
    try:
        await db.update_chat_setting(chat_id, log_enabled=True)
        return True
    except Exception:
        return False

async def disable_loge(chat_id: int) -> bool:
    """إلغاء تفعيل السجلات"""
    try:
        await db.update_chat_setting(chat_id, log_enabled=False)
        return True
    except Exception:
        return False

# وظائف الترحيب (Welcome)
async def is_welcome_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل الترحيب"""
    try:
        settings = await db.get_chat_settings(chat_id)
        return getattr(settings, 'welcome_enabled', True)
    except Exception:
        return True

async def enable_welcome(chat_id: int) -> bool:
    """تفعيل الترحيب"""
    try:
        await db.update_chat_setting(chat_id, welcome_enabled=True)
        return True
    except Exception:
        return False

async def disable_welcome(chat_id: int) -> bool:
    """إلغاء تفعيل الترحيب"""
    try:
        await db.update_chat_setting(chat_id, welcome_enabled=False)
        return True
    except Exception:
        return False

# وظائف البحث العام
async def is_search_enabled1() -> bool:
    """التحقق من تفعيل البحث العام"""
    try:
        return await db.get_temp_state("global_search_enabled", True)
    except Exception:
        return True

async def enable_search1() -> bool:
    """تفعيل البحث العام"""
    try:
        await db.set_temp_state("global_search_enabled", True)
        return True
    except Exception:
        return False

async def disable_search1() -> bool:
    """إلغاء تفعيل البحث العام"""
    try:
        await db.set_temp_state("global_search_enabled", False)
        return True
    except Exception:
        return False

# وظائف البحث في المجموعات
async def is_search_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل البحث في المجموعة"""
    try:
        settings = await db.get_chat_settings(chat_id)
        return getattr(settings, 'search_enabled', True)
    except Exception:
        return True

async def enable_search(chat_id: int) -> bool:
    """تفعيل البحث في المجموعة"""
    try:
        await db.update_chat_setting(chat_id, search_enabled=True)
        return True
    except Exception:
        return False

async def disable_search(chat_id: int) -> bool:
    """إلغاء تفعيل البحث في المجموعة"""
    try:
        await db.update_chat_setting(chat_id, search_enabled=False)
        return True
    except Exception:
        return False

# وظائف النشاط
async def is_active_chat(chat_id: int) -> bool:
    """التحقق من نشاط المحادثة"""
    try:
        return chat_id in active or True  # نظام مبسط - جميع المحادثات نشطة
    except Exception:
        return True

async def add_active_chat(chat_id: int):
    """إضافة محادثة نشطة"""
    try:
        if chat_id not in active:
            active.append(chat_id)
    except Exception:
        pass

async def remove_active_chat(chat_id: int):
    """إزالة محادثة نشطة"""
    try:
        if chat_id in active:
            active.remove(chat_id)
    except Exception:
        pass

async def add_active_video_chat(chat_id: int):
    """إضافة محادثة فيديو نشطة"""
    try:
        if chat_id not in activevideo:
            activevideo.append(chat_id)
    except Exception:
        pass

async def remove_active_video_chat(chat_id: int):
    """إزالة محادثة فيديو نشطة"""
    try:
        if chat_id in activevideo:
            activevideo.remove(chat_id)
    except Exception:
        pass

# وظائف الحسابات المساعدة
async def get_assistant_number(chat_id: int) -> str:
    """الحصول على رقم المساعد"""
    try:
        # التحقق من الذاكرة المؤقتة أولاً
        if chat_id in assistantdict:
            return str(assistantdict[chat_id])
        
        # الحصول من قاعدة البيانات
        settings = await db.get_chat_settings(chat_id)
        assistant_id = getattr(settings, 'assistant_id', 1)
        
        # حفظ في الذاكرة المؤقتة
        assistantdict[chat_id] = assistant_id
        return str(assistant_id)
    except Exception:
        return "1"

async def set_assistant_number(chat_id: int, assistant_id: int) -> bool:
    """تعيين رقم المساعد"""
    try:
        # حفظ في قاعدة البيانات
        await db.update_chat_setting(chat_id, assistant_id=assistant_id)
        
        # تحديث الذاكرة المؤقتة
        assistantdict[chat_id] = assistant_id
        return True
    except Exception:
        return False

# وظائف الصيانة
async def is_maintenance() -> bool:
    """التحقق من وضع الصيانة"""
    try:
        return await db.get_temp_state("maintenance_mode", False)
    except Exception:
        return False

async def maintenance_on() -> bool:
    """تفعيل وضع الصيانة"""
    try:
        await db.set_temp_state("maintenance_mode", True)
        if "maintenance" not in maintenance:
            maintenance.append("maintenance")
        return True
    except Exception:
        return False

async def maintenance_off() -> bool:
    """إلغاء وضع الصيانة"""
    try:
        await db.set_temp_state("maintenance_mode", False)
        if "maintenance" in maintenance:
            maintenance.remove("maintenance")
        return True
    except Exception:
        return False

# وظائف أنماط التشغيل
async def get_playmode(chat_id: int) -> str:
    """الحصول على نمط التشغيل"""
    try:
        if chat_id in playmode:
            return playmode[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        mode = getattr(settings, 'play_mode', 'Everyone')
        playmode[chat_id] = mode
        return mode
    except Exception:
        return "Everyone"

async def set_playmode(chat_id: int, mode: str) -> bool:
    """تعيين نمط التشغيل"""
    try:
        await db.update_chat_setting(chat_id, play_mode=mode)
        playmode[chat_id] = mode
        return True
    except Exception:
        return False

# وظائف نوع التشغيل
async def get_playtype(chat_id: int) -> str:
    """الحصول على نوع التشغيل"""
    try:
        if chat_id in playtype:
            return playtype[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        ptype = getattr(settings, 'play_type', 'Audio')
        playtype[chat_id] = ptype
        return ptype
    except Exception:
        return "Audio"

async def set_playtype(chat_id: int, ptype: str) -> bool:
    """تعيين نوع التشغيل"""
    try:
        await db.update_chat_setting(chat_id, play_type=ptype)
        playtype[chat_id] = ptype
        return True
    except Exception:
        return False

# وظائف التكرار
async def get_loop(chat_id: int) -> int:
    """الحصول على نمط التكرار"""
    try:
        if chat_id in loop:
            return loop[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        loop_mode = getattr(settings, 'loop_mode', 0)
        loop[chat_id] = loop_mode
        return loop_mode
    except Exception:
        return 0

async def set_loop(chat_id: int, loop_mode: int) -> bool:
    """تعيين نمط التكرار"""
    try:
        await db.update_chat_setting(chat_id, loop_mode=loop_mode)
        loop[chat_id] = loop_mode
        return True
    except Exception:
        return False

# وظائف الإيقاف المؤقت
async def is_paused(chat_id: int) -> bool:
    """التحقق من حالة الإيقاف المؤقت"""
    return chat_id in pause

async def pause_stream(chat_id: int):
    """إيقاف التشغيل مؤقتاً"""
    if chat_id not in pause:
        pause.append(chat_id)

async def resume_stream(chat_id: int):
    """استئناف التشغيل"""
    if chat_id in pause:
        pause.remove(chat_id)

# وظائف العد
async def get_count(chat_id: int) -> int:
    """الحصول على العدد"""
    return count.get(chat_id, 0)

async def set_count(chat_id: int, value: int):
    """تعيين العدد"""
    count[chat_id] = value

async def increment_count(chat_id: int) -> int:
    """زيادة العدد"""
    current = count.get(chat_id, 0)
    count[chat_id] = current + 1
    return count[chat_id]

# وظائف ربط القنوات
async def get_channelconnect(chat_id: int) -> Optional[int]:
    """الحصول على القناة المربوطة"""
    try:
        if chat_id in channelconnect:
            return channelconnect[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        channel_id = getattr(settings, 'connected_channel', None)
        
        if channel_id:
            channelconnect[chat_id] = channel_id
        
        return channel_id
    except Exception:
        return None

async def set_channelconnect(chat_id: int, channel_id: int) -> bool:
    """ربط قناة"""
    try:
        await db.update_chat_setting(chat_id, connected_channel=channel_id)
        channelconnect[chat_id] = channel_id
        return True
    except Exception:
        return False

async def remove_channelconnect(chat_id: int) -> bool:
    """إلغاء ربط القناة"""
    try:
        await db.update_chat_setting(chat_id, connected_channel=None)
        if chat_id in channelconnect:
            del channelconnect[chat_id]
        return True
    except Exception:
        return False

# وظائف اللغة
async def get_lang(chat_id: int) -> str:
    """الحصول على لغة المجموعة"""
    try:
        if chat_id in langm:
            return langm[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        language = getattr(settings, 'language', 'ar')
        langm[chat_id] = language
        return language
    except Exception:
        return 'ar'

async def set_lang(chat_id: int, language: str) -> bool:
    """تعيين لغة المجموعة"""
    try:
        await db.update_chat_setting(chat_id, language=language)
        langm[chat_id] = language
        return True
    except Exception:
        return False

# وظائف nonadmin
async def is_nonadmin_chat(chat_id: int) -> bool:
    """التحقق من السماح لغير المشرفين"""
    try:
        if chat_id in nonadmin:
            return nonadmin[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        allow_nonadmin = getattr(settings, 'allow_nonadmin', False)
        nonadmin[chat_id] = allow_nonadmin
        return allow_nonadmin
    except Exception:
        return False

async def set_nonadmin(chat_id: int, allow: bool) -> bool:
    """تعيين السماح لغير المشرفين"""
    try:
        await db.update_chat_setting(chat_id, allow_nonadmin=allow)
        nonadmin[chat_id] = allow
        return True
    except Exception:
        return False

# وظائف skipmode
async def get_skipmode(chat_id: int) -> str:
    """الحصول على نمط التخطي"""
    try:
        if chat_id in skipmode:
            return skipmode[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        skip_mode = getattr(settings, 'skip_mode', 'Admin')
        skipmode[chat_id] = skip_mode
        return skip_mode
    except Exception:
        return 'Admin'

async def set_skipmode(chat_id: int, mode: str) -> bool:
    """تعيين نمط التخطي"""
    try:
        await db.update_chat_setting(chat_id, skip_mode=mode)
        skipmode[chat_id] = mode
        return True
    except Exception:
        return False

# وظائف autoend
async def is_autoend_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل الإنهاء التلقائي"""
    try:
        if chat_id in autoend:
            return autoend[chat_id]
        
        settings = await db.get_chat_settings(chat_id)
        auto_end = getattr(settings, 'auto_end', True)
        autoend[chat_id] = auto_end
        return auto_end
    except Exception:
        return True

async def set_autoend(chat_id: int, enabled: bool) -> bool:
    """تعيين الإنهاء التلقائي"""
    try:
        await db.update_chat_setting(chat_id, auto_end=enabled)
        autoend[chat_id] = enabled
        return True
    except Exception:
        return False

# وظائف إضافية للتوافق
async def get_authuser_names(chat_id: int) -> List[str]:
    """الحصول على أسماء المستخدمين المصرح لهم"""
    try:
        settings = await db.get_chat_settings(chat_id)
        auth_users = getattr(settings, 'auth_users', [])
        return auth_users if isinstance(auth_users, list) else []
    except Exception:
        return []

async def get_cmode(chat_id: int) -> Optional[int]:
    """الحصول على نمط القناة"""
    return await get_channelconnect(chat_id)

async def get_upvote_count(chat_id: int) -> int:
    """الحصول على عدد التصويتات الإيجابية"""
    try:
        settings = await db.get_chat_settings(chat_id)
        return getattr(settings, 'upvote_count', 0)
    except Exception:
        return 0

# وظائف تنظيف الذاكرة
async def clear_memory_cache():
    """تنظيف ذاكرة التخزين المؤقت"""
    try:
        global active, activevideo, assistantdict, autoend, count
        global channelconnect, langm, loop, maintenance, nonadmin
        global pause, playmode, playtype, skipmode
        
        # تنظيف القوائم
        active.clear()
        activevideo.clear()
        maintenance.clear()
        pause.clear()
        
        # تنظيف القواميس
        assistantdict.clear()
        autoend.clear()
        count.clear()
        channelconnect.clear()
        langm.clear()
        loop.clear()
        nonadmin.clear()
        playmode.clear()
        playtype.clear()
        skipmode.clear()
        
        return True
    except Exception:
        return False

# وظائف الإحصائيات
async def get_database_stats() -> Dict[str, Any]:
    """الحصول على إحصائيات قاعدة البيانات"""
    try:
        return {
            'active_chats': len(active),
            'active_video_chats': len(activevideo),
            'cached_assistants': len(assistantdict),
            'paused_chats': len(pause),
            'connected_channels': len(channelconnect),
            'cached_languages': len(langm),
            'cached_loop_modes': len(loop),
            'cached_play_modes': len(playmode),
            'cached_play_types': len(playtype),
            'cached_skip_modes': len(skipmode),
            'maintenance_mode': len(maintenance) > 0
        }
    except Exception:
        return {}

# وظائف الصحة والفحص
async def health_check() -> Dict[str, bool]:
    """فحص صحة قاعدة البيانات"""
    try:
        # فحص الاتصال بقاعدة البيانات
        db_status = await db.health_check() if hasattr(db, 'health_check') else True
        
        return {
            'database_connection': db_status,
            'memory_cache_active': True,
            'maintenance_mode': await is_maintenance()
        }
    except Exception:
        return {
            'database_connection': False,
            'memory_cache_active': False,
            'maintenance_mode': False
        }