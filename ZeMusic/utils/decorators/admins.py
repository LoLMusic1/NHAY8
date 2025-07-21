from functools import wraps
from typing import Union

from ZeMusic.pyrogram_compatibility import InlineKeyboardButton, InlineKeyboardMarkup
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.misc import SUDOERS, db
from ZeMusic.utils.database import (
    get_authuser_names,
    get_cmode,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_maintenance,
    is_nonadmin_chat,
)
from config import SUPPORT_CHAT, adminlist, confirmer
from strings import get_string

# دالة بسيطة للتحقق من الصلاحيات
async def is_admin_or_owner(chat_id: int, user_id: int) -> bool:
    """التحقق من كون المستخدم مدير أو مالك"""
    try:
        # التحقق من SUDOERS أولاً
        if user_id in SUDOERS:
            return True
            
        # استخدام Telethon للتحقق من الصلاحيات
        bot_client = telethon_manager.bot_client
        if not bot_client:
            return False
            
        # الحصول على معلومات المشارك
        participant = await bot_client(GetParticipantRequest(
            channel=chat_id,
            participant=user_id
        ))
        
        # التحقق من نوع المشارك
        return isinstance(participant.participant, (
            ChannelParticipantAdmin,
            ChannelParticipantCreator
        ))
        
    except Exception:
        # في حالة الخطأ، نسمح فقط لـ SUDOERS
        return user_id in SUDOERS

# دالة مبسطة للتحقق من الصيانة
def maintenance_check(func):
    """Decorator للتحقق من وضع الصيانة"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if await is_maintenance():
            # في حالة Telethon events
            if hasattr(args[0], 'reply'):
                await args[0].reply("🔧 البوت تحت الصيانة حالياً")
                return
        return await func(*args, **kwargs)
    return wrapper

# دالة مبسطة للتحقق من صلاحيات الإدارة
def admin_check(func):
    """Decorator للتحقق من صلاحيات الإدارة"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # في حالة Telethon events
        if hasattr(args[0], 'sender_id') and hasattr(args[0], 'chat_id'):
            event = args[0]
            if not await is_admin_or_owner(event.chat_id, event.sender_id):
                await event.reply("❌ هذا الأمر للمديرين فقط")
                return
        return await func(*args, **kwargs)
    return wrapper

# Decorators مبسطة للتوافق مع الكود القديم
def AdminRightsCheck(func):
    """Decorator مبسط للتحقق من حقوق الإدارة"""
    return admin_check(func)

def AdminActual(func):
    """Decorator مبسط للتحقق من الإدارة الفعلية"""
    return admin_check(func)

def PlayingOrNot(func):
    """Decorator للتحقق من حالة التشغيل"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # منطق بسيط - يمكن تطويره لاحقاً
        return await func(*args, **kwargs)
    return wrapper

# التوافق مع الكود القديم
AdminRightsCheck = AdminRightsCheck
AdminActual = AdminActual

# دوال مساعدة للتوافق
async def member_permissions(chat_id: int, user_id: int):
    """دالة للحصول على صلاحيات العضو"""
    try:
        return await is_admin_or_owner(chat_id, user_id)
    except:
        return False

# إضافة الاستيرادات المطلوبة لـ Telethon
try:
    from telethon.tl.functions.channels import GetParticipantRequest
    from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
except ImportError:
    # في حالة عدم توفر Telethon
    async def is_admin_or_owner(chat_id: int, user_id: int) -> bool:
        return user_id in SUDOERS
