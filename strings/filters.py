# -*- coding: utf-8 -*-
"""
Telethon Filters - مرشحات بسيطة مع Telethon
"""

from telethon import events

class TelethonFilters:
    """مرشحات Telethon بسيطة"""
    
    @staticmethod
    def private():
        """رسائل خاصة"""
        def filter_func(event):
            return event.is_private
        return filter_func
    
    @staticmethod
    def group():
        """رسائل المجموعات"""
        def filter_func(event):
            return event.is_group
        return filter_func
    
    @staticmethod
    def channel():
        """رسائل القنوات"""
        def filter_func(event):
            return event.is_channel and not event.is_group
        return filter_func
    
    @staticmethod
    def text():
        """رسائل نصية"""
        def filter_func(event):
            return hasattr(event, 'message') and event.message and hasattr(event.message, 'text') and event.message.text
        return filter_func
    
    @staticmethod
    def command(commands):
        """أوامر محددة"""
        if isinstance(commands, str):
            commands = [commands]
        
        def filter_func(event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            text = event.message.text.strip()
            return any(text.startswith(f'/{cmd}') for cmd in commands)
        return filter_func
    
    @staticmethod
    def regex(pattern):
        """نمط regex"""
        import re
        compiled_pattern = re.compile(pattern)
        
        def filter_func(event):
            if not hasattr(event, 'message') or not event.message or not hasattr(event.message, 'text'):
                return False
            return bool(compiled_pattern.search(event.message.text))
        return filter_func
    
    @staticmethod
    def user(user_ids):
        """مستخدمين محددين"""
        if isinstance(user_ids, (int, str)):
            user_ids = [user_ids]
        
        def filter_func(event):
            return event.sender_id in user_ids
        return filter_func

# إنشاء مثيل
filters = TelethonFilters()

other_filters = filters.group & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, "")
