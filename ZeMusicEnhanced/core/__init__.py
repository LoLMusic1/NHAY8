#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Core Module
تاريخ الإنشاء: 2025-01-28

النواة الأساسية للبوت - جميع الأنظمة الأساسية
"""

from .telethon_client import TelethonClient, TelethonClientManager
from .database import DatabaseManager, ChatSettings, UserData, ChatData, AssistantData

# استيرادات اختيارية - ستتم إضافتها تدريجياً
try:
    from .assistant_manager import AssistantManager
except ImportError:
    AssistantManager = None

try:
    from .music_engine import MusicEngine
except ImportError:
    MusicEngine = None

try:
    from .security_manager import SecurityManager
except ImportError:
    SecurityManager = None

try:
    from .performance_monitor import PerformanceMonitor
except ImportError:
    PerformanceMonitor = None

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
    # Core Classes
    'TelethonClient',
    'TelethonClientManager', 
    'DatabaseManager',
    
    # Optional Classes
    'AssistantManager',
    'MusicEngine',
    'SecurityManager',
    'PerformanceMonitor',
    
    # Data Classes
    'ChatSettings',
    'UserData', 
    'ChatData',
    'AssistantData',
    
    # Global Managers
    'telethon_client_manager',
    'database_manager'
]