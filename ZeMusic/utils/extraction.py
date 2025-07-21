from ZeMusic.pyrogram_compatibility import enums, types
from ZeMusic.core.telethon_client import telethon_manager


async def extract_user(m: 'types.Message') -> 'types.User':
    """استخراج المستخدم من الرسالة باستخدام Telethon"""
    try:
        if m.reply_to_message:
            return m.reply_to_message.from_user
        
        # في حالة عدم وجود reply، نحاول استخراج من النص
        if hasattr(m, 'entities') and m.entities:
            msg_entities = m.entities[1] if m.text.startswith("/") else m.entities[0]
            
            # استخدام Telethon للحصول على المستخدم
            bot_client = telethon_manager.bot_client
            if bot_client:
                if msg_entities.type == enums.MessageEntityType.TEXT_MENTION:
                    user_id = msg_entities.user.id
                else:
                    # محاولة استخراج من الأمر
                    command_parts = m.text.split()
                    if len(command_parts) > 1:
                        user_ref = command_parts[1]
                        if user_ref.isdecimal():
                            user_id = int(user_ref)
                        else:
                            user_id = user_ref
                    else:
                        return None
                
                # الحصول على المستخدم من Telethon
                try:
                    entity = await bot_client.get_entity(user_id)
                    return types.User(
                        id=entity.id,
                        first_name=getattr(entity, 'first_name', ''),
                        username=getattr(entity, 'username', None)
                    )
                except Exception:
                    return None
        
        return None
        
    except Exception:
        return None
