from ZeMusic.pyrogram_compatibility import InlineKeyboardButton
import config

Lnk= "https://t.me/" + config.CHANNEL_LINK

def get_bot_username():
    """الحصول على username البوت"""
    try:
        # استخدام BOT_USERNAME من config أو افتراضي
        return getattr(config, 'BOT_USERNAME', 'ZeMusicBot').replace('@', '')
    except:
        return 'ZeMusicBot'

def start_panel(_):
    bot_username = get_bot_username()
    buttons = [
        [
            InlineKeyboardButton(
                text="أضفني إلى مجموعتك",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton(text="الأوامر", callback_data="zzzback")],
        [
            InlineKeyboardButton(text="𝐃𝐞𝐯", user_id=config.OWNER_ID),
            InlineKeyboardButton(text=config.CHANNEL_NAME, url=Lnk),
        ],
    ]
    return buttons


def private_panel(_):
    bot_username = get_bot_username()
    buttons = [
        [
            InlineKeyboardButton(
                text="أضفني إلى مجموعتك",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton(text="الأوامر", callback_data="zzzback")],
        [
            InlineKeyboardButton(text="𝐃𝐞𝐯", user_id=config.OWNER_ID),
            InlineKeyboardButton(text=config.CHANNEL_NAME, url=Lnk),
        ],
    ]
    return buttons
