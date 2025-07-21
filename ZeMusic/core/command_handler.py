import asyncio
import json
from typing import Dict, Any, Callable, Optional

import config
from ZeMusic.logging import LOGGER
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.plugins.bot.basic_commands import command_handler as basic_commands
from ZeMusic.plugins.owner.admin_panel import admin_panel
from ZeMusic.plugins.owner.stats_handler import stats_handler
from ZeMusic.plugins.owner.broadcast_handler import broadcast_handler
from ZeMusic.plugins.owner.owner_panel import owner_panel

class TelethonCommandHandler:
    """معالج الأوامر والcallbacks مع Telethon"""
    
    def __init__(self):
        self.commands = {}
        self.callback_handlers = {}
        self.message_handlers = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر والcallbacks"""
        # تسجيل الأوامر الأساسية
        self.commands = {
            '/start': self.handle_start,
            '/help': self.handle_help,
            '/play': self.handle_play,
            '/pause': self.handle_pause,
            '/resume': self.handle_resume,
            '/stop': self.handle_stop,
            '/skip': self.handle_skip,
            '/current': self.handle_current,
            '/queue': self.handle_queue,
            '/owner': self.handle_owner,
            '/stats': self.handle_stats,
            '/admin': self.handle_admin,
        }
        
        # تسجيل معالجات الcallbacks
        self.callback_handlers = {
            'admin_': self.handle_admin_callback,
            'broadcast_': self.handle_broadcast_callback,
            'owner_': self.handle_owner_callback,
            'stats_': self.handle_stats_callback,
        }
    
    async def handle_message(self, event):
        """معالج الرسائل الواردة من Telethon"""
        try:
            message = event.message
            text = message.text or ""
            chat_id = event.chat_id
            sender_id = event.sender_id
            message_id = message.id
            
            # تحويل للتنسيق المتوافق
            mock_update = self._create_mock_update_from_telethon(event)
            
            # فحص الاشتراك الإجباري
            should_check_subscription = False
            
            is_private_chat = chat_id > 0
            is_group_or_channel = chat_id < 0
            
            # قواعد فحص الاشتراك
            if sender_id == config.OWNER_ID:
                should_check_subscription = False
            elif text.startswith('/admin') or text.startswith('/owner'):
                should_check_subscription = False
            elif text == '/start':
                should_check_subscription = False
            elif is_private_chat:
                should_check_subscription = True
            elif is_group_or_channel:
                is_bot_command = text.startswith('/')
                is_bot_mention = f"@{telethon_manager.bot_client.me.username}" in text if telethon_manager.bot_client else False
                is_reply_to_bot = message.reply_to_msg_id and hasattr(message.reply_to, 'sender_id') and message.reply_to.sender_id == int(config.BOT_ID)
                
                bot_keywords = [
                    'شغل', 'تشغيل', 'play', 'ايقاف', 'وقف', 'stop', 'pause', 'resume',
                    'تخطي', 'skip', 'next', 'تالي', 'قائمة', 'queue', 'موسيقى', 'music',
                    'صوت', 'audio', 'video', 'فيديو', 'بحث', 'search'
                ]
                is_using_bot_keywords = any(keyword in text.lower() for keyword in bot_keywords)
                
                should_check_subscription = is_bot_command or is_bot_mention or is_reply_to_bot or is_using_bot_keywords
            
            # فحص الاشتراك إذا لزم الأمر
            if should_check_subscription and config.FORCE_SUB_CHANNEL:
                from ZeMusic.core.database import db
                is_subscribed = await self._check_subscription(sender_id, config.FORCE_SUB_CHANNEL)
                if not is_subscribed:
                    await self._send_subscription_message(mock_update)
                    return
            
            # إضافة المستخدم والمحادثة لقاعدة البيانات
            from ZeMusic.core.database import db
            await db.add_user(sender_id)
            await db.add_chat(chat_id)
            
            # معالجة الأوامر
            if text.startswith('/'):
                command = text.split()[0].lower()
                if command in self.commands:
                    await self.commands[command](mock_update)
                    return
            
            # معالجة الرسائل العادية
            await self._handle_normal_message(mock_update)
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج الرسائل: {e}")
    
    async def handle_callback_query(self, event):
        """معالج الاستعلامات المضمنة من Telethon"""
        try:
            data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
            chat_id = getattr(event, 'chat_id', None)
            sender_id = getattr(event, 'sender_id', None)
            message_id = None
            
            # التحقق من وجود message بشكل آمن
            if hasattr(event, 'message') and event.message:
                message_id = getattr(event.message, 'id', None)
            
            # تحويل للتنسيق المتوافق
            mock_callback = self._create_mock_callback_from_telethon(event)
            
            # العثور على معالج مناسب
            for prefix, handler in self.callback_handlers.items():
                if data.startswith(prefix):
                    await handler(mock_callback)
                    return
            
            # معالج افتراضي
            await self._handle_unknown_callback(mock_callback)
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج الcallbacks: {e}")
    
    def _create_mock_update_from_telethon(self, event):
        """تحويل حدث Telethon إلى تنسيق متوافق"""
        class MockUpdate:
            def __init__(self, event):
                self.message = MockMessage(event)
                self.effective_chat = MockChat(event.chat_id)
                self.effective_user = MockUser(event.sender_id)
                self.effective_message = self.message
                self.sender_id = event.sender_id
                self.chat_id = event.chat_id
                self.event = event
                
            async def reply(self, text, **kwargs):
                """إضافة دالة reply للتوافق"""
                return await self.event.reply(text, **kwargs)
        
        class MockMessage:
            def __init__(self, event):
                # التحقق الآمن من الخصائص
                if hasattr(event, 'message') and event.message:
                    self.text = getattr(event.message, 'text', '') or ""
                    self.message_id = getattr(event.message, 'id', 0)
                    self.date = getattr(event.message, 'date', None)
                    reply_to_msg_id = getattr(event.message, 'reply_to_msg_id', None)
                else:
                    self.text = ""
                    self.message_id = 0
                    self.date = None
                    reply_to_msg_id = None
                
                self.chat = MockChat(getattr(event, 'chat_id', 0))
                self.from_user = MockUser(getattr(event, 'sender_id', 0))
                self.reply_to_message = None
                if reply_to_msg_id:
                    self.reply_to_message = MockMessage(event)
        
        class MockChat:
            def __init__(self, chat_id):
                self.id = chat_id
                self.type = "private" if chat_id > 0 else "group"
        
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
                self.username = None
                self.first_name = "User"
        
        return MockUpdate(event)
    
    def _create_mock_callback_from_telethon(self, event):
        """تحويل callback من Telethon إلى تنسيق متوافق"""
        class MockCallback:
            def __init__(self, event):
                self.data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
                self.message = MockMessage(event)
                self.from_user = MockUser(getattr(event, 'sender_id', 0))
                self.id = str(getattr(event, 'query_id', 0))
        
        class MockMessage:
            def __init__(self, event):
                # التحقق الآمن من الخصائص
                if hasattr(event, 'message') and event.message:
                    self.message_id = getattr(event.message, 'id', 0)
                    self.text = getattr(event.message, 'text', '')
                else:
                    self.message_id = 0
                    self.text = ''
                
                self.chat = MockChat(getattr(event, 'chat_id', 0))
        
        class MockChat:
            def __init__(self, chat_id):
                self.id = chat_id
        
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
        
        return MockCallback(event)
    
    async def _check_subscription(self, user_id: int, channel: str) -> bool:
        """فحص اشتراك المستخدم في القناة"""
        try:
            if not telethon_manager.bot_client:
                return True
            
            # محاولة الحصول على عضوية المستخدم
            try:
                member = await telethon_manager.bot_client.get_entity(user_id)
                if member:
                    # فحص العضوية في القناة
                    try:
                        participants = await telethon_manager.bot_client.get_participants(channel, limit=1, search=str(user_id))
                        return len(participants) > 0
                    except:
                        return True  # في حالة الخطأ، نسمح بالوصول
                return False
            except:
                return True
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص الاشتراك: {e}")
            return True
    
    async def _send_subscription_message(self, update):
        """إرسال رسالة الاشتراك الإجباري"""
        try:
            subscription_text = config.FORCE_SUB_TEXT.format(
                SUPPORT_CHAT=config.SUPPORT_CHAT or "@YourSupport"
            )
            
            # في حالة عدم وجود نص مخصص، استخدم الافتراضي
            if not hasattr(config, 'FORCE_SUB_TEXT'):
                subscription_text = f"""
🔒 **عذراً، يجب الاشتراك أولاً!**

للاستفادة من خدمات البوت، يجب الاشتراك في القناة الرسمية:
👇 **اضغط على الزر للاشتراك** 👇

بعد الاشتراك، ارسل الأمر مرة أخرى.

📞 **للدعم:** {config.SUPPORT_CHAT or '@YourSupport'}
                """
            
            # إرسال الرسالة (سيتم تنفيذها بواسطة المعالج المناسب)
            pass
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إرسال رسالة الاشتراك: {e}")
    
    async def handle_start(self, update):
        """معالج أمر /start"""
        try:
            # استخدام معالج مباشر بدلاً من start_pm
            from ZeMusic.utils.inline.start import private_panel
            from ZeMusic.pyrogram_compatibility import InlineKeyboardMarkup
            from ZeMusic.utils.database import get_lang, add_served_user
            from strings import get_string
            import config
            
            # إضافة المستخدم
            await add_served_user(update.sender_id)
            
            # الحصول على اللغة
            language = await get_lang(update.sender_id)
            _ = get_string(language)
            
            # إنشاء الأزرار
            buttons_data = private_panel(_)
            
            # تحويل إلى أزرار Telethon
            from telethon import Button
            buttons = []
            for row in buttons_data:
                button_row = []
                for btn in row:
                    if hasattr(btn, 'url') and btn.url:
                        button_row.append(Button.url(btn.text, btn.url))
                    elif hasattr(btn, 'user_id') and btn.user_id:
                        button_row.append(Button.mention(btn.text, btn.user_id))
                    elif hasattr(btn, 'callback_data') and btn.callback_data:
                        button_row.append(Button.inline(btn.text, data=btn.callback_data))
                    else:
                        # زر عادي بدون callback
                        button_row.append(Button.inline(btn.text, data="default"))
                buttons.append(button_row)
            
            # إرسال الرسالة
            try:
                # الحصول على معلومات البوت
                bot_username = "ZeMusicBot"  # افتراضي
                try:
                    bot_me = await self.bot_client.get_me()
                    if bot_me and bot_me.username:
                        bot_username = bot_me.username
                except:
                    pass
                
                # الحصول على اسم المستخدم بشكل آمن
                user_name = "المستخدم"
                if hasattr(update, 'sender') and update.sender:
                    user_name = getattr(update.sender, 'first_name', 'المستخدم')
                elif hasattr(update, 'effective_user') and update.effective_user:
                    user_name = getattr(update.effective_user, 'first_name', 'المستخدم')
                
                user_mention = f"[{user_name}](tg://user?id={getattr(update, 'sender_id', 0)})"
                
                # استخدام النص الافتراضي إذا لم تتوفر الترجمة
                try:
                    caption = _["start_2"].format(user_mention, f"@{bot_username}")
                except:
                    caption = f"🎵 **مرحباً بك في ZeMusic Bot!**\n\n👋 أهلاً {user_mention}\n\n🎶 بوت تشغيل الموسيقى في المكالمات الصوتية\n\n💡 استخدم /help لعرض الأوامر\n\n🤖 البوت: @{bot_username}"
                
                await update.reply(
                    caption,
                    file=config.START_IMG_URL,
                    buttons=buttons
                )
                
            except Exception as e:
                # في حالة فشل إرسال الصورة، نرسل نص فقط
                await update.reply(
                    f"🎵 **مرحباً بك في ZeMusic Bot!**\n\n"
                    f"👋 أهلاً {update.sender.first_name or 'المستخدم'}\n\n"
                    f"🎶 بوت تشغيل الموسيقى في المكالمات الصوتية\n\n"
                    f"💡 استخدم /help لعرض الأوامر\n\n"
                    f"🤖 البوت: @{bot_username}",
                    buttons=buttons
                )
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /start: {e}")
            try:
                await update.reply("❌ حدث خطأ في معالجة الأمر")
            except:
                pass
    
    async def handle_help(self, update):
        """معالج أمر /help"""
        try:
            # استخدام دالة موجودة بدلاً من دالة غير موجودة
            await update.reply("📚 **مرحباً بك في ZeMusic Bot**\n\n🎵 بوت تشغيل الموسيقى في المكالمات الصوتية\n\n💡 الأوامر الأساسية:\n• `/play` - تشغيل موسيقى\n• `/pause` - إيقاف مؤقت\n• `/resume` - استكمال\n• `/stop` - إيقاف\n• `/skip` - تخطي\n\n👨‍💼 للمطورين:\n• `/owner` - لوحة المطور\n• `/cookies` - إدارة cookies")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /help: {e}")
    
    async def handle_play(self, update):
        """معالج أمر /play"""
        try:
            # رسالة مؤقتة حتى يتم تطوير النظام كاملاً
            await update.reply("🎵 **خدمة تشغيل الموسيقى**\n\n⚠️ النظام قيد التطوير\n\n💡 سيتم إضافة هذه الخدمة قريباً")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /play: {e}")
    
    async def handle_pause(self, update):
        """معالج أمر /pause"""
        try:
            await update.reply("⏸️ **إيقاف مؤقت**\n\n⚠️ النظام قيد التطوير")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /pause: {e}")
    
    async def handle_resume(self, update):
        """معالج أمر /resume"""
        try:
            await update.reply("▶️ **استكمال التشغيل**\n\n⚠️ النظام قيد التطوير")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /resume: {e}")
    
    async def handle_stop(self, update):
        """معالج أمر /stop"""
        try:
            await update.reply("⏹️ **إيقاف التشغيل**\n\n⚠️ النظام قيد التطوير")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /stop: {e}")
    
    async def handle_skip(self, update):
        """معالج أمر /skip"""
        try:
            await update.reply("⏭️ **تخطي الأغنية**\n\n⚠️ النظام قيد التطوير")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /skip: {e}")
    
    async def handle_current(self, update):
        """معالج أمر /current"""
        try:
            await update.reply("🎵 **الأغنية الحالية**\n\n⚠️ لا يوجد تشغيل حالياً")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /current: {e}")
    
    async def handle_queue(self, update):
        """معالج أمر /queue"""
        try:
            await update.reply("📜 **قائمة الانتظار**\n\n⚠️ القائمة فارغة")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /queue: {e}")
    
    async def handle_owner(self, update):
        """معالج أمر /owner"""
        try:
            await owner_panel.handle_owner_command(update)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /owner: {e}")
    
    async def handle_stats(self, update):
        """معالج أمر /stats"""
        try:
            await stats_handler.handle_stats_command(update)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /stats: {e}")
    
    async def handle_admin(self, update):
        """معالج أمر /admin"""
        try:
            await admin_panel.handle_admin_command(update)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /admin: {e}")
    
    async def handle_admin_callback(self, callback):
        """معالج callbacks لوحة الإدارة"""
        try:
            await admin_panel.handle_callback(callback)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج admin callback: {e}")
    
    async def handle_broadcast_callback(self, callback):
        """معالج callbacks البث"""
        try:
            await broadcast_handler.handle_callback(callback)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج broadcast callback: {e}")
    
    async def handle_owner_callback(self, callback):
        """معالج callbacks المالك"""
        try:
            await owner_panel.handle_callback(callback)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج owner callback: {e}")
    
    async def handle_stats_callback(self, callback):
        """معالج callbacks الإحصائيات"""
        try:
            await stats_handler.handle_callback(callback)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج stats callback: {e}")
    
    async def _handle_normal_message(self, update):
        """معالج الرسائل العادية"""
        try:
            # معالجة إضافة الحسابات المساعدة
            if hasattr(update, 'message') and update.message and hasattr(update.message, 'text'):
                user_id = getattr(update, 'sender_id', 0)
                message_text = update.message.text.strip()
                
                # التحقق من أن هذا session string
                # سجل محاولة الفحص
                if user_id == config.OWNER_ID:
                    LOGGER(__name__).info(f"🔍 فحص رسالة من المالك: طول={len(message_text)}")
                
                # شروط session string أوسع
                is_session_string = (
                    user_id == config.OWNER_ID and 
                    len(message_text) > 150 and  # session strings عادة طويلة
                    (
                        '1BVtsOHU' in message_text or  # علامة Telethon session
                        'BQA' in message_text or       # علامة أخرى
                        'BAA' in message_text or       # علامة أخرى  
                        'AQAA' in message_text or      # علامة أخرى
                        len(message_text) > 300        # أو طول كبير جداً
                    )
                )
                
                if is_session_string:
                    LOGGER(__name__).info(f"✅ تم اكتشاف session string من المالك")
                    
                    try:
                        from ZeMusic.plugins.owner.owner_panel import owner_panel
                        
                        # معالجة session string
                        LOGGER(__name__).info(f"🔄 بدء معالجة session string...")
                        result = await owner_panel.process_add_assistant_input(user_id, message_text)
                        LOGGER(__name__).info(f"📊 نتيجة المعالجة: {result}")
                        
                        if result and result.get('success'):
                            keyboard_data = result.get('keyboard', [])
                            if keyboard_data:
                                # تحويل إلى أزرار Telethon
                                from telethon import Button
                                buttons = []
                                for row in keyboard_data:
                                    button_row = []
                                    for btn in row:
                                        button_row.append(Button.inline(btn['text'], data=btn['callback_data']))
                                    buttons.append(button_row)
                                await update.reply(result['message'], buttons=buttons)
                            else:
                                await update.reply(result['message'])
                        else:
                            await update.reply(result.get('message', '❌ حدث خطأ في المعالجة'))
                            
                    except Exception as e:
                        LOGGER(__name__).error(f"خطأ في معالجة session string: {e}")
                        await update.reply("❌ حدث خطأ في معالجة session string")
                        
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج الرسائل العادية: {e}")
    
    async def _handle_unknown_callback(self, callback):
        """معالج الcallbacks غير المعروفة"""
        try:
            LOGGER(__name__).warning(f"Callback غير معروف: {callback.data}")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج الcallback غير المعروف: {e}")

# المثيل العام
telethon_command_handler = TelethonCommandHandler()