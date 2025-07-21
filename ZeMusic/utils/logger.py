from ZeMusic.pyrogram_compatibility import enums
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    """إرسال سجلات التشغيل باستخدام Telethon"""
    if await is_on_off(2):
        if message.from_user:
            ne = "تم التشغيل في المجموعة"
            user_id = message.from_user.id
            user_mention = message.from_user.mention
            user_username = message.from_user.username
        else:
            ne = "تم التشغيل في القناة"
            user_id = "مجهول"
            user_mention = "مجهول"
            user_username = "مجهول"
        
        logger_text = f"""
<b>{ne}</b>

<b>شات ايدي :</b> <code>{message.chat.id}</code>
<b>الاسم :</b> {message.chat.title}
<b>اليوزر :</b> @{message.chat.username}

<b>ايدي :</b> <code>{user_id}</code>
<b>الاسم :</b> {user_mention}
<b>يوزر :</b> @{user_username}

<b>الاغنيه :</b> {message.text.split(None, 1)[1]}
<b>اسم المشغل :</b> {streamtype}"""
        
        if message.chat.id != LOGGER_ID:
            try:
                # استخدام Telethon لإرسال الرسالة
                bot_client = telethon_manager.bot_client
                if bot_client:
                    await bot_client.send_message(
                        entity=LOGGER_ID,
                        message=logger_text,
                        parse_mode='html',
                        link_preview=False
                    )
            except Exception as e:
                # تجاهل أخطاء السجلات
                pass
        return
