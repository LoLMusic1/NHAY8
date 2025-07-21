# -*- coding: utf-8 -*-
"""
طبقة توافق Telethon - بديل بسيط لـ pyrogram_compatibility
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
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
        else:
            self.text = ''
            self.chat = MockChat(0)
            self.from_user = MockUser(0)
            self.message_id = 0
    
    async def reply(self, text, **kwargs):
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

# مرشحات للتوافق
class filters:
    @staticmethod
    def private():
        def filter_func(_, __, event):
            return hasattr(event, 'is_private') and event.is_private
        return filter_func
    
    @staticmethod
    def group():
        def filter_func(_, __, event):
            return hasattr(event, 'is_group') and event.is_group
        return filter_func
    
    @staticmethod
    def command(commands, prefixes="/"):
        if isinstance(commands, str):
            commands = [commands]
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        
        def filter_func(_, __, event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            text = event.message.text.strip()
            for prefix in prefixes:
                for cmd in commands:
                    if text.startswith(f"{prefix}{cmd}"):
                        return True
            return False
        return filter_func
    
    @staticmethod
    def regex(pattern):
        import re
        compiled_pattern = re.compile(pattern)
        
        def filter_func(_, __, event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            return bool(compiled_pattern.search(event.message.text))
        return filter_func
    
    @staticmethod
    def user(user_ids):
        if isinstance(user_ids, (int, str)):
            user_ids = [user_ids]
        
        def filter_func(_, __, event):
            return hasattr(event, 'sender_id') and event.sender_id in user_ids
        return filter_func

# للتوافق مع InputMediaPhoto
class InputMediaPhoto:
    def __init__(self, media, caption="", **kwargs):
        self.media = media
        self.caption = caption

# للتوافق mع InlineQueryResult
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

# كلاس عميل للتوافق
class Client:
    def __init__(self, *args, **kwargs):
        self.client = telethon_manager.bot_client if telethon_manager else None
    
    def on_message(self, filters=None):
        def decorator(func):
            # تسجيل المعالج مع telethon_manager
            return func
        return decorator
    
    def on_callback_query(self, filters=None):
        def decorator(func):
            return func
        return decorator

# للتوافق مع emoji
class emoji:
    FIRE = "🔥"
    MUSICAL_NOTE = "🎵"
    CHECK_MARK = "✅"
    CROSS_MARK = "❌"

# تصدير app
app = telethon_manager.bot_client if telethon_manager else None