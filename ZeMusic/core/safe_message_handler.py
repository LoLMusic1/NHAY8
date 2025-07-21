import asyncio
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

# إعداد السجل
logger = logging.getLogger(__name__)

class SafeMessageHandler:
    """معالج رسائل آمن ومحمي من timeout"""
    
    def __init__(self):
        self.timeout_limit = 3.0  # حد زمني قصير
    
    async def handle_message_safely(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج آمن للرسائل مع حماية من timeout"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # التحقق من صحة البيانات
            if not message_text or not user_id:
                return
            
            # معالجة آمنة مع timeout
            try:
                await asyncio.wait_for(
                    self._process_message(update, context, user_id, message_text),
                    timeout=self.timeout_limit
                )
            except asyncio.TimeoutError:
                logger.warning(f"Message processing timed out for user {user_id}")
                await update.message.reply_text(
                    "⏱️ **انتهت مهلة المعالجة**\n\n"
                    "الرجاء المحاولة مرة أخرى",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Message processing error for user {user_id}: {e}")
                await update.message.reply_text(
                    "❌ **حدث خطأ مؤقت**\n\n"
                    "الرجاء المحاولة مرة أخرى",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Critical error in message handler: {e}")
    
    async def _process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message_text: str):
        """معالجة الرسالة الفعلية"""
        
        # محاولة تحميل المدير الواقعي
        realistic_manager = None
        try:
            from ZeMusic.core.realistic_assistant_manager import realistic_assistant_manager
            realistic_manager = realistic_assistant_manager
        except ImportError:
            logger.warning("Realistic assistant manager not available")
        
        # معالجة الرسائل حسب الحالة
        if realistic_manager and hasattr(realistic_manager, 'user_states'):
            if user_id in realistic_manager.user_states:
                user_state = realistic_manager.user_states[user_id]
                current_state = user_state.get('state', '')
                
                if current_state == 'waiting_phone':
                    await realistic_manager.handle_phone_input(update, context)
                    return
                elif current_state == 'waiting_code':
                    await realistic_manager.handle_code_input(update, context)
                    return
                elif current_state == 'waiting_password':
                    await realistic_manager.handle_password_input(update, context)
                    return
        
        # رسالة افتراضية للرسائل العادية
        if message_text.startswith('/'):
            await update.message.reply_text(
                "❓ **أمر غير معروف**\n\n"
                "استخدم `/start` للدخول إلى القائمة الرئيسية",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "💬 **مرحباً!**\n\n"
                "استخدم `/start` للدخول إلى القائمة الرئيسية",
                parse_mode='Markdown'
            )

# مثيل المعالج الآمن
safe_message_handler = SafeMessageHandler()