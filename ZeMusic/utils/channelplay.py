from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.utils.database import get_cmode


async def get_channeplayCB(_, command, CallbackQuery):
    if command == "c":
        chat_id = await get_cmode(CallbackQuery.message.chat.id)
        if chat_id is None:
            try:
                return await CallbackQuery.answer(_["setting_7"], show_alert=True)
            except:
                return
        try:
            # استخدام Telethon بدلاً من Pyrogram
            bot_client = telethon_manager.bot_client
            if bot_client:
                entity = await bot_client.get_entity(chat_id)
                channel = entity.title
            else:
                channel = "Channel"
        except:
            try:
                return await CallbackQuery.answer(_["cplay_4"], show_alert=True)
            except:
                return
    else:
        channel = CallbackQuery.message.chat.title
    return channel
