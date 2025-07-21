"""
ملف التوافق الشامل لاستبدال pyrogram بـ TDLib
يتم استيراده بدلاً من pyrogram في جميع الملفات
"""

from .compatibility import (
    CompatibilityClient as Client, 
    TDLibFilters,
    enums,
    errors,
    app,
    __version__
)

# إنشاء كائن filters عام
filters = TDLibFilters()

# إضافة types للتوافق الكامل
class types:
    class Message:
        def __init__(self, **kwargs):
            self.text = kwargs.get('text', '')
            self.chat = kwargs.get('chat')
            self.from_user = kwargs.get('from_user')
            self.message_id = kwargs.get('message_id')
            self.reply_to_message = kwargs.get('reply_to_message')
    
    class CallbackQuery:
        def __init__(self, **kwargs):
            self.data = kwargs.get('data', '')
            self.from_user = kwargs.get('from_user')
            self.message = kwargs.get('message')
    
    class InlineQuery:
        def __init__(self, **kwargs):
            self.query = kwargs.get('query', '')
            self.from_user = kwargs.get('from_user')
    
    class User:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id')
            self.first_name = kwargs.get('first_name', '')
            self.username = kwargs.get('username')
    
    class Chat:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id')
            self.title = kwargs.get('title', '')
            self.type = kwargs.get('type', '')
    
    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard=None, **kwargs):
            self.inline_keyboard = inline_keyboard or []
    
    class InlineKeyboardButton:
        def __init__(self, text, **kwargs):
            self.text = text
            self.url = kwargs.get('url')
            self.callback_data = kwargs.get('callback_data')
            self.switch_inline_query = kwargs.get('switch_inline_query')
    
    class ReplyKeyboardMarkup:
        def __init__(self, keyboard=None, **kwargs):
            self.keyboard = keyboard or []
            self.resize_keyboard = kwargs.get('resize_keyboard', True)
            self.one_time_keyboard = kwargs.get('one_time_keyboard', False)
    
    class InlineQueryResultArticle:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id')
            self.title = kwargs.get('title', '')
            self.description = kwargs.get('description', '')
            self.input_message_content = kwargs.get('input_message_content')
    
    class InputTextMessageContent:
        def __init__(self, message_text, **kwargs):
            self.message_text = message_text
            self.parse_mode = kwargs.get('parse_mode')
    
    class InputMediaPhoto:
        def __init__(self, media, **kwargs):
            self.media = media
            self.caption = kwargs.get('caption', '')
    
    class Voice:
        def __init__(self, **kwargs):
            self.file_id = kwargs.get('file_id')
            self.duration = kwargs.get('duration', 0)
    
    class ChatPrivileges:
        def __init__(self, **kwargs):
            self.can_manage_chat = kwargs.get('can_manage_chat', False)
            self.can_delete_messages = kwargs.get('can_delete_messages', False)
            self.can_manage_video_chats = kwargs.get('can_manage_video_chats', False)
            self.can_restrict_members = kwargs.get('can_restrict_members', False)
    
    class ChatMember:
        def __init__(self, **kwargs):
            self.user = kwargs.get('user')
            self.status = kwargs.get('status')
            self.permissions = kwargs.get('permissions')
    
    class ReplyKeyboardRemove:
        def __init__(self, selective=False):
            self.selective = selective
    
    class InlineQueryResultPhoto:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id')
            self.photo_url = kwargs.get('photo_url')
            self.thumbnail_url = kwargs.get('thumbnail_url')
            self.title = kwargs.get('title', '')
            self.description = kwargs.get('description', '')

# متغير emoji للتوافق
emoji = "🎵"

# إضافة enums للتوافق
class ChatMemberStatus:
    ADMINISTRATOR = "administrator"
    BANNED = "banned"
    LEFT = "left"
    MEMBER = "member"
    OWNER = "creator"
    RESTRICTED = "restricted"

class MessageEntityType:
    URL = "url"
    TEXT_LINK = "text_link" 
    MENTION = "mention"
    HASHTAG = "hashtag"
    CASHTAG = "cashtag"
    BOT_COMMAND = "bot_command"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    CODE = "code"
    PRE = "pre"

class ChatType:
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"

class ChatMembersFilter:
    ALL = "all"
    BANNED = "banned"
    RESTRICTED = "restricted"
    ADMINISTRATORS = "administrators"
    BOTS = "bots"

class ChatAction:
    TYPING = "typing"
    UPLOAD_PHOTO = "upload_photo"
    RECORD_VIDEO = "record_video"
    UPLOAD_VIDEO = "upload_video"
    RECORD_VOICE = "record_voice"
    UPLOAD_VOICE = "upload_voice"
    UPLOAD_DOCUMENT = "upload_document"
    CHOOSE_STICKER = "choose_sticker"
    FIND_LOCATION = "find_location"
    RECORD_VIDEO_NOTE = "record_video_note"
    UPLOAD_VIDEO_NOTE = "upload_video_note"

class ParseMode:
    DEFAULT = None
    MARKDOWN = "Markdown"
    HTML = "HTML"

class enums:
    ChatMemberStatus = ChatMemberStatus
    MessageEntityType = MessageEntityType
    ChatType = ChatType
    ChatMembersFilter = ChatMembersFilter
    ChatAction = ChatAction
    ParseMode = ParseMode

# إضافة errors للتوافق
class errors:
    class ChatAdminRequired(Exception):
        pass
    
    class InviteRequestSent(Exception):
        pass
        
    class UserAlreadyParticipant(Exception):
        pass
        
    class UserNotParticipant(Exception):
        pass
    
    class FloodWait(Exception):
        def __init__(self, value):
            self.value = value
            super().__init__(f"FloodWait: {value}")
    
    class MessageNotModified(Exception):
        pass
    
    class MessageIdInvalid(Exception):
        pass
    
    class ChatWriteForbidden(Exception):
        pass

# دالة decorator للتوافق
def on_message(filters_obj):
    """محاكاة @app.on_message decorator"""
    def decorator(func):
        return func
    return decorator

def on_callback_query(filters_obj=None):
    """محاكاة @app.on_callback_query decorator"""
    def decorator(func):
        return func
    return decorator

def on_inline_query():
    """محاكاة @app.on_inline_query decorator"""
    def decorator(func):
        return func
    return decorator

# إضافة app methods للتوافق
app.on_message = on_message
app.on_callback_query = on_callback_query
app.on_inline_query = on_inline_query

# إضافة الكلاسات للاستيراد المباشر
InlineKeyboardButton = types.InlineKeyboardButton
InlineKeyboardMarkup = types.InlineKeyboardMarkup
ReplyKeyboardMarkup = types.ReplyKeyboardMarkup
InlineQueryResultArticle = types.InlineQueryResultArticle
InputTextMessageContent = types.InputTextMessageContent
InputMediaPhoto = types.InputMediaPhoto
Voice = types.Voice
Message = types.Message
CallbackQuery = types.CallbackQuery
User = types.User
Chat = types.Chat

# تصدير enums و types للتوافق
enums = enums
MessageEntityType = MessageEntityType
ChatType = ChatType
ChatMembersFilter = ChatMembersFilter
ChatAction = ChatAction
ParseMode = ParseMode
FloodWait = errors.FloodWait
MessageNotModified = errors.MessageNotModified
MessageIdInvalid = errors.MessageIdInvalid
ChatAdminRequired = errors.ChatAdminRequired
UserNotParticipant = errors.UserNotParticipant
UserAlreadyParticipant = errors.UserAlreadyParticipant
ChatWriteForbidden = errors.ChatWriteForbidden
ChatPrivileges = types.ChatPrivileges
ChatMember = types.ChatMember
ReplyKeyboardRemove = types.ReplyKeyboardRemove
InlineQueryResultPhoto = types.InlineQueryResultPhoto

# إضافة CompatibilityClient للتوافق مع call.py
class CompatibilityClient:
    """عميل توافق مع Telethon"""
    def __init__(self, *args, **kwargs):
        pass
    
    def on_message(self, filters_obj):
        """محاكاة @app.on_message decorator"""
        def decorator(func):
            return func
        return decorator
    
    def on_callback_query(self, filters_obj=None):
        """محاكاة @app.on_callback_query decorator"""
        def decorator(func):
            return func
        return decorator
    
    def on_inline_query(self):
        """محاكاة @app.on_inline_query decorator"""
        def decorator(func):
            return func
        return decorator
    
    def on_edited_message(self, filters_obj=None):
        """محاكاة @app.on_edited_message decorator"""
        def decorator(func):
            return func
        return decorator