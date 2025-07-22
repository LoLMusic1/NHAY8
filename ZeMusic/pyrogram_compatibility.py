# -*- coding: utf-8 -*-
"""
طبقة توافق Telethon - بديل متطور لـ Pyrogram
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Union, Callable
from telethon import Button, events, TelegramClient
from telethon.tl.types import Message as TelethonMessage, User as TelethonUser, Chat as TelethonChat
from ZeMusic.core.telethon_client import telethon_manager

# إصدار وهمي للتوافق
__version__ = "1.4.0"

# للتوافق مع Pyrogram
class Message:
    """رسالة وهمية للتوافق مع Pyrogram"""
    def __init__(self, event=None):
        self.event = event
        if event and hasattr(event, 'message'):
            self.text = getattr(event.message, 'text', '')
            self.chat = MockChat(event.chat_id if hasattr(event, 'chat_id') else 0)
            self.from_user = MockUser(event.sender_id if hasattr(event, 'sender_id') else 0)
            self.message_id = getattr(event.message, 'id', 0)
            self.document = getattr(event.message, 'document', None)
            self.caption = getattr(event.message, 'message', '')
        else:
            self.text = ''
            self.chat = MockChat(0)
            self.from_user = MockUser(0)
            self.message_id = 0
            self.document = None
            self.caption = ''
    
    async def reply(self, text, **kwargs):
        if self.event:
            return await self.event.reply(text, **kwargs)
    
    async def reply_text(self, text, **kwargs):
        if self.event:
            return await self.event.reply(text, **kwargs)

class MockChat:
    """محادثة وهمية للتوافق"""
    def __init__(self, chat_id):
        self.id = chat_id
        self.type = "private" if chat_id > 0 else "group"

class MockUser:
    """مستخدم وهمي للتوافق"""
    def __init__(self, user_id):
        self.id = user_id
        self.first_name = "User"
        self.username = None
        self.mention = f"[User](tg://user?id={user_id})"

class CallbackQuery:
    """استعلام callback وهمي للتوافق"""
    def __init__(self, event=None):
        self.event = event
        if event:
            self.from_user = MockUser(event.sender_id)
            self.data = event.data.decode('utf-8') if hasattr(event, 'data') else ""
            self.message = Message(event)
    
    async def answer(self, text="", show_alert=False):
        if self.event:
            await self.event.answer(text, alert=show_alert)

# إعدادات enums للتوافق
class enums:
    class ChatType:
        PRIVATE = "private"
        GROUP = "group"
        SUPERGROUP = "supergroup"
        CHANNEL = "channel"
    
    class ChatMemberStatus:
        OWNER = "creator"
        ADMINISTRATOR = "administrator"
        MEMBER = "member"
        RESTRICTED = "restricted"
        LEFT = "left"
        BANNED = "kicked"
    
    class ParseMode:
        DEFAULT = None
        MARKDOWN = "markdown"
        HTML = "html"
    
    class MessageEntityType:
        TEXT_MENTION = "text_mention"
        URL = "url"
        TEXT_LINK = "text_link"
        MENTION = "mention"
        HASHTAG = "hashtag"
        BOT_COMMAND = "bot_command"

# أزرار للتوافق
def InlineKeyboardButton(text, callback_data=None, url=None, **kwargs):
    """إنشاء زر inline للتوافق مع Pyrogram"""
    if callback_data:
        return Button.inline(text, callback_data.encode('utf-8') if isinstance(callback_data, str) else callback_data)
    elif url:
        return Button.url(text, url)
    else:
        return Button.inline(text, b"default")

def InlineKeyboardMarkup(buttons):
    """إنشاء keyboard markup للتوافق مع Pyrogram"""
    if not buttons:
        return None
    
    # تحويل الأزرار إلى صيغة Telethon
    telethon_buttons = []
    for row in buttons:
        if isinstance(row, list):
            telethon_buttons.append(row)
        else:
            telethon_buttons.append([row])
    
    return telethon_buttons

# للتوافق مع ReplyKeyboardMarkup
def ReplyKeyboardMarkup(buttons, **kwargs):
    """keyboard عادي للتوافق"""
    return buttons

def ReplyKeyboardRemove():
    """إزالة keyboard للتوافق"""
    return None

# استثناءات للتوافق
class errors:
    class FloodWait(Exception):
        def __init__(self, value):
            self.value = value
    
    class MessageNotModified(Exception):
        pass
    
    class MessageIdInvalid(Exception):
        pass
    
    class ChatAdminRequired(Exception):
        pass
    
    class UserNotParticipant(Exception):
        pass
    
    class UserAlreadyParticipant(Exception):
        pass
    
    class ChatWriteForbidden(Exception):
        pass

# كلاسات للتوافق
FloodWait = errors.FloodWait
MessageNotModified = errors.MessageNotModified
MessageIdInvalid = errors.MessageIdInvalid
ChatAdminRequired = errors.ChatAdminRequired
UserNotParticipant = errors.UserNotParticipant
UserAlreadyParticipant = errors.UserAlreadyParticipant
ChatWriteForbidden = errors.ChatWriteForbidden

# أنواع أخرى للتوافق
class types:
    Message = Message
    CallbackQuery = CallbackQuery
    User = MockUser
    Chat = MockChat

class ChatMembersFilter:
    ALL = "all"
    KICKED = "kicked"
    RESTRICTED = "restricted"
    BOTS = "bots"
    RECENT = "recent"
    ADMINISTRATORS = "administrators"

ChatMemberStatus = enums.ChatMemberStatus
ChatType = enums.ChatType
ParseMode = enums.ParseMode
MessageEntityType = enums.MessageEntityType

# فلتر مركب للدعم
class CombinedFilter:
    """فلتر مركب يدعم العمليات المنطقية"""
    def __init__(self, filter_func):
        self.filter_func = filter_func
    
    def __call__(self, event):
        return self.filter_func(event)
    
    def __and__(self, other):
        """عملية AND"""
        def combined_filter(event):
            if callable(other):
                return self.filter_func(event) and other(event)
            elif hasattr(other, 'filter_func'):
                return self.filter_func(event) and other.filter_func(event)
            else:
                return self.filter_func(event) and other
        return CombinedFilter(combined_filter)
    
    def __or__(self, other):
        """عملية OR"""
        def combined_filter(event):
            if callable(other):
                return self.filter_func(event) or other(event)
            elif hasattr(other, 'filter_func'):
                return self.filter_func(event) or other.filter_func(event)
            else:
                return self.filter_func(event) or other
        return CombinedFilter(combined_filter)
    
    def __invert__(self):
        """عملية NOT"""
        def inverted_filter(event):
            return not self.filter_func(event)
        return CombinedFilter(inverted_filter)

# مرشحات للتوافق
class filters:
    @staticmethod
    def private():
        def filter_func(event):
            return hasattr(event, 'is_private') and event.is_private
        return CombinedFilter(filter_func)
    
    @staticmethod
    def group():
        def filter_func(event):
            return hasattr(event, 'is_group') and event.is_group
        return CombinedFilter(filter_func)
    
    @staticmethod
    def channel():
        def filter_func(event):
            return hasattr(event, 'is_channel') and event.is_channel and not event.is_group
        return CombinedFilter(filter_func)
    
    @staticmethod
    def command(commands, prefixes="/"):
        if isinstance(commands, str):
            commands = [commands]
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        
        def filter_func(event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            text = event.message.text.strip()
            for prefix in prefixes:
                for cmd in commands:
                    if text.startswith(f"{prefix}{cmd}"):
                        return True
            return False
        return CombinedFilter(filter_func)
    
    @staticmethod
    def regex(pattern):
        compiled_pattern = re.compile(pattern)
        
        def filter_func(event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            return bool(compiled_pattern.search(event.message.text))
        return CombinedFilter(filter_func)
    
    @staticmethod
    def user(user_ids):
        if isinstance(user_ids, (int, str)):
            user_ids = [user_ids]
        
        def filter_func(event):
            return hasattr(event, 'sender_id') and event.sender_id in user_ids
        return CombinedFilter(filter_func)
    
    @staticmethod
    def text():
        def filter_func(event):
            return (hasattr(event, 'message') and event.message and 
                   hasattr(event.message, 'text') and event.message.text)
        return CombinedFilter(filter_func)
    
    @staticmethod
    def document():
        def filter_func(event):
            return (hasattr(event, 'message') and event.message and 
                   hasattr(event.message, 'document') and event.message.document)
        return CombinedFilter(filter_func)
    
    @staticmethod
    def new_chat_members():
        def filter_func(event):
            return hasattr(event, 'user_added') and event.user_added
        return CombinedFilter(filter_func)
    
    @staticmethod
    def left_chat_member():
        def filter_func(event):
            return hasattr(event, 'user_left') and event.user_left
        return CombinedFilter(filter_func)
    
    @staticmethod
    def video_chat_started():
        def filter_func(event):
            return hasattr(event, 'action') and 'video_chat_started' in str(type(event.action))
        return CombinedFilter(filter_func)
    
    @staticmethod
    def video_chat_ended():
        def filter_func(event):
            return hasattr(event, 'action') and 'video_chat_ended' in str(type(event.action))
        return CombinedFilter(filter_func)
    
    @staticmethod
    def video_chat_members_invited():
        def filter_func(event):
            return hasattr(event, 'action') and 'video_chat_members_invited' in str(type(event.action))
        return CombinedFilter(filter_func)

# للتوافق مع InputMediaPhoto
class InputMediaPhoto:
    def __init__(self, media, caption="", **kwargs):
        self.media = media
        self.caption = caption

# للتوافق مع InlineQueryResult
class InlineQueryResultArticle:
    def __init__(self, title, input_message_content, **kwargs):
        self.title = title
        self.input_message_content = input_message_content

class InputTextMessageContent:
    def __init__(self, message_text, **kwargs):
        self.message_text = message_text

# للتوافق مع ChatAction
class ChatAction:
    TYPING = "typing"
    UPLOAD_PHOTO = "upload_photo"
    UPLOAD_DOCUMENT = "upload_document"
    UPLOAD_AUDIO = "upload_audio"

# للتوافق مع ChatPrivileges
class ChatPrivileges:
    def __init__(self, **kwargs):
        pass

class ChatMember:
    def __init__(self, **kwargs):
        pass

# معالج الأوامر المحسن
class TelethonAppHandler:
    """معالج الأوامر مع Telethon"""
    
    def __init__(self):
        self.handlers = {}
        self.callback_handlers = {}
        self._pending_handlers = []
        self._pending_callbacks = []
    
    @property
    def client(self):
        """الحصول على العميل الحالي"""
        if telethon_manager and telethon_manager.bot_client:
            return telethon_manager.bot_client
        return None
    
    def _register_pending_handlers(self):
        """تسجيل المعالجات المؤجلة عند توفر العميل"""
        if not self.client:
            return
            
        for filters_func, func in self._pending_handlers:
            @self.client.on(events.NewMessage())
            async def handler(event, original_func=func, filter_func=filters_func):
                try:
                    # فحص المرشحات
                    if filter_func and not filter_func(event):
                        return
                    
                    # إنشاء كائن Message للتوافق
                    message = Message(event)
                    
                    # استدعاء الدالة الأصلية
                    await original_func(self.client, message, {}, event.chat_id)
                except Exception as e:
                    print(f"خطأ في معالج الرسالة: {e}")
        
        for filters_func, func in self._pending_callbacks:
            @self.client.on(events.CallbackQuery())
            async def handler(event, original_func=func, filter_func=filters_func):
                try:
                    # فحص المرشحات
                    if filter_func and not filter_func(event):
                        return
                    
                    # إنشاء كائن CallbackQuery للتوافق
                    callback = CallbackQuery(event)
                    
                    # استدعاء الدالة الأصلية
                    await original_func(self.client, callback)
                except Exception as e:
                    print(f"خطأ في معالج الcallback: {e}")
        
        # تفريغ القوائم المؤجلة
        self._pending_handlers.clear()
        self._pending_callbacks.clear()
    
    def on_message(self, filters_func=None, group=0):
        """مزخرف لمعالجة الرسائل"""
        def decorator(func):
            if self.client:
                # تسجيل فوري إذا كان العميل متاح
                @self.client.on(events.NewMessage())
                async def handler(event):
                    try:
                        # فحص المرشحات
                        if filters_func and not filters_func(event):
                            return
                        
                        # إنشاء كائن Message للتوافق
                        message = Message(event)
                        
                        # استدعاء الدالة الأصلية
                        await func(self.client, message, {}, event.chat_id)
                    except Exception as e:
                        print(f"خطأ في معالج الرسالة: {e}")
            else:
                # تأجيل التسجيل إذا لم يكن العميل متاح
                self._pending_handlers.append((filters_func, func))
                
            return func
        return decorator
    
    def on_callback_query(self, filters_func=None):
        """مزخرف لمعالجة الcallbacks"""
        def decorator(func):
            if self.client:
                # تسجيل فوري إذا كان العميل متاح
                @self.client.on(events.CallbackQuery())
                async def handler(event):
                    try:
                        # فحص المرشحات
                        if filters_func and not filters_func(event):
                            return
                        
                        # إنشاء كائن CallbackQuery للتوافق
                        callback = CallbackQuery(event)
                        
                        # استدعاء الدالة الأصلية
                        await func(self.client, callback)
                    except Exception as e:
                        print(f"خطأ في معالج الcallback: {e}")
            else:
                # تأجيل التسجيل إذا لم يكن العميل متاح
                self._pending_callbacks.append((filters_func, func))
                
            return func
        return decorator

# للتوافق مع emoji
class emoji:
    FIRE = "🔥"
    MUSICAL_NOTE = "🎵"
    CHECK_MARK = "✅"
    CROSS_MARK = "❌"

# دالة command للتوافق مع strings.filters
def command(commands):
    """دالة command للتوافق مع strings.filters"""
    return filters.command(commands)

# إنشاء مثيل app
app = TelethonAppHandler()

# دعم BANNED_USERS كمرشح
try:
    import config
    original_banned_users = getattr(config, 'BANNED_USERS', [])
    # تحويل BANNED_USERS إلى مرشح
    BANNED_USERS = CombinedFilter(lambda event: hasattr(event, 'sender_id') and event.sender_id in original_banned_users)
except (ImportError, AttributeError):
    # إذا لم يكن متاح، إنشاء مرشح فارغ
    BANNED_USERS = CombinedFilter(lambda event: False)

# تصدير العميل
if telethon_manager and telethon_manager.bot_client:
    app.client = telethon_manager.bot_client