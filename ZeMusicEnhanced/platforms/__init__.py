#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Platforms Module
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Enhanced Edition

مدير المنصات الموسيقية المحسن
"""

from .platform_manager import PlatformManager
from .youtube import YouTubePlatform
from .spotify import SpotifyPlatform
from .soundcloud import SoundCloudPlatform
from .apple_music import AppleMusicPlatform

__all__ = [
    'PlatformManager',
    'YouTubePlatform',
    'SpotifyPlatform', 
    'SoundCloudPlatform',
    'AppleMusicPlatform'
]