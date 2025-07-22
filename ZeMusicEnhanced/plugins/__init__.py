#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Plugins System
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Enhanced Edition

نظام البلاجين والإضافات المحسن
"""

from .live_stream import LiveStreamPlugin
from .channel_play import ChannelPlayPlugin  
from .force_subscribe import ForceSubscribePlugin
from .group_management import GroupManagementPlugin
from .developer_commands import DeveloperCommandsPlugin

__all__ = [
    'LiveStreamPlugin',
    'ChannelPlayPlugin',
    'ForceSubscribePlugin', 
    'GroupManagementPlugin',
    'DeveloperCommandsPlugin'
]