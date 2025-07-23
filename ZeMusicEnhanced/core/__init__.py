#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Core Module
تاريخ الإنشاء: 2025-01-28

النواة الأساسية للبوت - جميع الأنظمة الأساسية
"""

from .telethon_client import TelethonClient, TelethonClientManager
from .database import DatabaseManager, ChatSettings, UserData, ChatData, AssistantData
from .call import TelethonCall, CallManager
from .music_manager import TelethonMusicManager, MusicSession, QueueItem
from .command_handler import CommandHandler, CommandRegistry
from .cookies_manager import CookiesManager
from .git import GitManager
from .handlers_registry import HandlersRegistry
from .simple_handlers import SimpleHandlers

# مدراء النظام الرئيسيين
telethon_client_manager = None  # سيتم تهيئته في الملف الرئيسي
database_manager = None
call_manager = None
music_manager = None
command_handler = None
cookies_manager = None
git_manager = None
handlers_registry = None

__all__ = [
    # Classes
    'TelethonClient',
    'TelethonClientManager', 
    'DatabaseManager',
    'TelethonCall',
    'CallManager',
    'TelethonMusicManager',
    'CommandHandler',
    'CommandRegistry',
    'CookiesManager',
    'GitManager',
    'HandlersRegistry',
    'SimpleHandlers',
    
    # Data Classes
    'ChatSettings',
    'UserData', 
    'ChatData',
    'AssistantData',
    'MusicSession',
    'QueueItem',
    
    # Global Managers
    'telethon_client_manager',
    'database_manager',
    'call_manager',
    'music_manager',
    'command_handler',
    'cookies_manager',
    'git_manager',
    'handlers_registry'
]