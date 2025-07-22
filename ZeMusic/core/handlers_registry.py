"""
تسجيل جميع معالجات البوت بعد التهيئة
"""

from ZeMusic.logging import LOGGER
from telethon import events

async def register_all_handlers(bot_client):
    """تسجيل جميع معالجات البوت"""
    try:
        # تسجيل معالج callbacks للمطور
        from ZeMusic.plugins.owner.owner_panel import handle_owner_callbacks
        bot_client.add_event_handler(handle_owner_callbacks, events.CallbackQuery)
        LOGGER(__name__).info("✅ تم تسجيل معالج callbacks المطور")
        
        # تسجيل معالج البحث المخصص (الأولوية الأعلى)
        from ZeMusic.plugins.play.download import search_command_handler
bot_client.add_event_handler(search_command_handler, events.NewMessage)
        LOGGER(__name__).info("✅ تم تسجيل معالج البحث المخصص")
        
        # تسجيل معالج التحميل المحسن (احتياطي)
        from ZeMusic.plugins.play.enhanced_handler import enhanced_smart_download_handler
        bot_client.add_event_handler(enhanced_smart_download_handler, events.NewMessage)
        LOGGER(__name__).info("✅ تم تسجيل معالج التحميل المحسن")
        
        # تسجيل معالج cookies callbacks
        bot_client.add_event_handler(handle_cookies_callbacks, events.CallbackQuery)
        LOGGER(__name__).info("✅ تم تسجيل معالج cookies callbacks")
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في تسجيل المعالجات: {e}")

async def handle_cookies_callbacks(event):
    """معالج callbacks أزرار cookies"""
    try:
        # التحقق من أن هذا callback query وليس رسالة عادية
        if not hasattr(event, 'data'):
            return
            
        # في Telethon v1.36+، event.data هو نص مباشرة
        data = event.data if isinstance(event.data, str) else event.data.decode('utf-8')
        
        if data.startswith('cookies_'):
            # استيراد المعالجات المطلوبة
            from ZeMusic.plugins.sudo.cookies_admin import (
                cookies_add_help_callback, cookies_delete_callback, 
                cookies_scan_callback, delete_file_callback,
                confirm_delete_callback
            )
            
            if data == "cookies_add_help":
                await cookies_add_help_callback(None, event)
            elif data == "cookies_delete":
                await cookies_delete_callback(None, event)
            elif data == "cookies_scan":
                await cookies_scan_callback(None, event)
            elif data.startswith("delete_file_"):
                await delete_file_callback(None, event)
            elif data.startswith("confirm_delete_"):
                await confirm_delete_callback(None, event)
                
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج cookies callbacks: {e}")