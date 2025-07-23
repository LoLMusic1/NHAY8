#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Admin Plugins
تاريخ الإنشاء: 2025-01-28

بلاجينز إدارة المجموعات والموسيقى
"""

from .auth import *
from .callback import *
from .loop import *
from .pause import *
from .resume import *
from .seek import *
from .shuffle import *
from .skip import *
from .speed import *
from .stop import *

__all__ = [
    # Auth management
    'add_auth_user',
    'remove_auth_user',
    'get_auth_users',
    
    # Callback handlers
    'admin_callback_handler',
    'music_callback_handler',
    
    # Playback controls
    'pause_stream',
    'resume_stream',
    'stop_stream',
    'skip_stream',
    'shuffle_queue',
    'set_loop_mode',
    'seek_stream',
    'change_speed',
    
    # Utilities
    'check_admin_permissions',
    'get_stream_info'
]