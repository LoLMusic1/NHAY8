#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Plugins Module
تاريخ الإنشاء: 2025-01-28

جميع بلاجينز البوت المتقدمة
"""

# Import all plugin modules
from . import admins
from . import bot  
from . import play
from . import sudo
from . import tools
from . import misc
from . import owner
from . import managed

# Plugin categories
ADMIN_PLUGINS = [
    'auth', 'callback', 'loop', 'pause', 'resume', 
    'seek', 'shuffle', 'skip', 'speed', 'stop'
]

BOT_PLUGINS = [
    'basic_commands', 'help', 'inline', 'settings', 
    'start', 'telethon_help', 'telethon_start'
]

PLAY_PLUGINS = [
    'play', 'download', 'live', 'channel', 'playmode',
    'filters', 'bot', 'developers', 'enhanced_handler'
]

SUDO_PLUGINS = [
    'autoend', 'blchat', 'block', 'gban', 'logger',
    'maintenance', 'restart', 'sudoers', 'cookies_admin'
]

TOOLS_PLUGINS = [
    'active', 'dev', 'language', 'ping', 'queue',
    'reload', 'speedtest', 'stats'
]

MISC_PLUGINS = [
    'autoleave', 'broadcast', 'seeker', 'watcher'
]

OWNER_PLUGINS = [
    'admin_panel', 'assistants_handler', 'broadcast_handler',
    'force_subscribe_handler', 'owner_panel', 'stats_handler'
]

MANAGED_PLUGINS = [
    'assistant_manager', 'bot_management', 'telegraph',
    'gpt_integration', 'call_monitor'
]

# Total plugins count
TOTAL_PLUGINS = (
    len(ADMIN_PLUGINS) + len(BOT_PLUGINS) + len(PLAY_PLUGINS) +
    len(SUDO_PLUGINS) + len(TOOLS_PLUGINS) + len(MISC_PLUGINS) +
    len(OWNER_PLUGINS) + len(MANAGED_PLUGINS)
)

__all__ = [
    'ADMIN_PLUGINS', 'BOT_PLUGINS', 'PLAY_PLUGINS', 'SUDO_PLUGINS',
    'TOOLS_PLUGINS', 'MISC_PLUGINS', 'OWNER_PLUGINS', 'MANAGED_PLUGINS',
    'TOTAL_PLUGINS'
]