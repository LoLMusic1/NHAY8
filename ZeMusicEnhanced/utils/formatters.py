#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Formatters
تاريخ الإنشاء: 2025-01-28

أدوات التنسيق والتحويل المحسنة
"""

import re
from typing import Union, Optional

def format_duration(seconds: Union[int, float]) -> str:
    """تحويل الثواني إلى تنسيق الوقت"""
    try:
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00"
        
        seconds = int(seconds)
        
        if seconds == 0:
            return "00:00"
        
        # حساب الساعات والدقائق والثواني
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
            
    except Exception:
        return "00:00"

def format_file_size(size_bytes: Union[int, float]) -> str:
    """تحويل حجم الملف إلى تنسيق قابل للقراءة"""
    try:
        if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
            return "0 B"
        
        # وحدات القياس
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
            
    except Exception:
        return "0 B"

def format_number(number: Union[int, float]) -> str:
    """تنسيق الأرقام مع فواصل الآلاف"""
    try:
        if not isinstance(number, (int, float)):
            return "0"
        
        if isinstance(number, float):
            if number.is_integer():
                number = int(number)
        
        return f"{number:,}"
        
    except Exception:
        return "0"

def format_percentage(value: Union[int, float], total: Union[int, float]) -> str:
    """حساب وتنسيق النسبة المئوية"""
    try:
        if not isinstance(value, (int, float)) or not isinstance(total, (int, float)):
            return "0%"
        
        if total == 0:
            return "0%"
        
        percentage = (value / total) * 100
        
        if percentage >= 100:
            return "100%"
        elif percentage < 0.1:
            return "<0.1%"
        else:
            return f"{percentage:.1f}%"
            
    except Exception:
        return "0%"

def format_bitrate(bitrate: Union[int, float]) -> str:
    """تنسيق معدل البت"""
    try:
        if not isinstance(bitrate, (int, float)) or bitrate <= 0:
            return "غير محدد"
        
        bitrate = int(bitrate)
        
        if bitrate >= 1000:
            return f"{bitrate // 1000}k"
        else:
            return f"{bitrate}"
            
    except Exception:
        return "غير محدد"

def format_quality_text(quality: str) -> str:
    """تنسيق نص الجودة"""
    try:
        quality_map = {
            'low': '🔴 منخفضة',
            'medium': '🟡 متوسطة', 
            'high': '🟢 عالية',
            'ultra': '🔵 فائقة'
        }
        
        return quality_map.get(quality.lower(), '⚪ غير محدد')
        
    except Exception:
        return '⚪ غير محدد'

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """اقتطاع النص مع إضافة نقاط في النهاية"""
    try:
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
        
    except Exception:
        return ""

def clean_text(text: str) -> str:
    """تنظيف النص من الرموز غير المرغوبة"""
    try:
        if not isinstance(text, str):
            return ""
        
        # إزالة HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # إزالة الأسطر الفارغة المتعددة
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    except Exception:
        return ""

def format_track_title(title: str, artist: str = "") -> str:
    """تنسيق عنوان المقطع مع الفنان"""
    try:
        if not title:
            return "عنوان غير معروف"
        
        # تنظيف العنوان
        clean_title = clean_text(title)
        
        # إضافة الفنان إذا كان متاحاً
        if artist and artist.strip():
            clean_artist = clean_text(artist)
            return f"{clean_artist} - {clean_title}"
        
        return clean_title
        
    except Exception:
        return "عنوان غير معروف"

def format_progress_bar(current: Union[int, float], total: Union[int, float], 
                       length: int = 20) -> str:
    """إنشاء شريط تقدم نصي"""
    try:
        if not isinstance(current, (int, float)) or not isinstance(total, (int, float)):
            return "▱" * length
        
        if total <= 0:
            return "▱" * length
        
        # حساب النسبة
        progress = min(current / total, 1.0)
        filled_length = int(length * progress)
        
        # إنشاء الشريط
        bar = "▰" * filled_length + "▱" * (length - filled_length)
        
        return bar
        
    except Exception:
        return "▱" * length

def format_platform_name(platform: str) -> str:
    """تنسيق اسم المنصة"""
    try:
        platform_names = {
            'youtube': '🔴 YouTube',
            'spotify': '🟢 Spotify',
            'soundcloud': '🟠 SoundCloud',
            'apple_music': '🎵 Apple Music',
            'resso': '🎧 Resso',
            'carbon': '⚫ Carbon',
            'telegram': '💙 Telegram'
        }
        
        return platform_names.get(platform.lower(), f'🎵 {platform.title()}')
        
    except Exception:
        return '🎵 غير محدد'

def format_time_ago(timestamp) -> str:
    """تنسيق الوقت المنقضي"""
    try:
        from datetime import datetime, timedelta
        
        if isinstance(timestamp, str):
            # محاولة تحويل النص إلى تاريخ
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return "غير محدد"
        
        if not isinstance(timestamp, datetime):
            return "غير محدد"
        
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        diff = now - timestamp
        
        if diff.days > 365:
            years = diff.days // 365
            return f"منذ {years} سنة" if years == 1 else f"منذ {years} سنوات"
        elif diff.days > 30:
            months = diff.days // 30
            return f"منذ {months} شهر" if months == 1 else f"منذ {months} أشهر"
        elif diff.days > 0:
            return f"منذ {diff.days} يوم" if diff.days == 1 else f"منذ {diff.days} أيام"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
        else:
            return "الآن"
            
    except Exception:
        return "غير محدد"

def format_emoji_number(number: int) -> str:
    """تحويل الرقم إلى رموز تعبيرية"""
    try:
        emoji_digits = {
            '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
            '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣'
        }
        
        result = ""
        for digit in str(number):
            result += emoji_digits.get(digit, digit)
        
        return result
        
    except Exception:
        return str(number)

def format_status_indicator(status: str) -> str:
    """تنسيق مؤشر الحالة"""
    try:
        status_indicators = {
            'online': '🟢 متصل',
            'offline': '🔴 غير متصل',
            'connecting': '🟡 جاري الاتصال',
            'error': '❌ خطأ',
            'maintenance': '🔧 صيانة',
            'active': '✅ نشط',
            'inactive': '⏸️ غير نشط',
            'playing': '▶️ يشغل',
            'paused': '⏸️ متوقف',
            'stopped': '⏹️ متوقف'
        }
        
        return status_indicators.get(status.lower(), f'⚪ {status}')
        
    except Exception:
        return '⚪ غير محدد'