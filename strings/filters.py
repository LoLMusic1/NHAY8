# -*- coding: utf-8 -*-
"""
Telethon Filters - مرشحات بسيطة مع Telethon
"""

from typing import Union, List
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
    
    @staticmethod
    def via_bot():
        """رسائل عبر بوت"""
        def filter_func(event):
            return hasattr(event.message, 'via_bot_id') and event.message.via_bot_id
        return filter_func
    
    @staticmethod
    def forwarded():
        """رسائل معاد توجيهها"""
        def filter_func(event):
            return hasattr(event.message, 'forward') and event.message.forward
        return filter_func

# إنشاء مثيل
filters = TelethonFilters()

# مرشحات مركبة
other_filters = lambda event: (filters.group()(event) and 
                              not filters.via_bot()(event) and 
                              not filters.forwarded()(event))

other_filters2 = lambda event: (filters.private()(event) and 
                               not filters.via_bot()(event) and 
                               not filters.forwarded()(event))

def command(commands: Union[str, List[str]]):
    """دالة مساعدة لإنشاء مرشح أوامر"""
    return filters.command(commands)
