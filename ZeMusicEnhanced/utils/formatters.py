#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Advanced Formatters
تاريخ الإنشاء: 2025-01-28

وظائف التنسيق المتقدمة
"""

import os
import re
import json
import math
import requests
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Union, Optional, List, Dict, Any

def format_duration(seconds: Union[int, float]) -> str:
    """تنسيق المدة الزمنية بشكل متقدم"""
    try:
        if not seconds or seconds <= 0:
            return "00:00"
        
        seconds = int(seconds)
        
        # حساب الوحدات الزمنية
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        # تنسيق حسب المدة
        if days > 0:
            return f"{days}د {hours:02d}:{minutes:02d}:{secs:02d}"
        elif hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
            
    except (ValueError, TypeError):
        return "00:00"

def format_file_size(bytes_size: Union[int, float]) -> str:
    """تنسيق حجم الملف بوحدات مناسبة"""
    try:
        if not bytes_size or bytes_size <= 0:
            return "0 B"
        
        bytes_size = float(bytes_size)
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        
        unit_index = 0
        while bytes_size >= 1024.0 and unit_index < len(units) - 1:
            bytes_size /= 1024.0
            unit_index += 1
        
        # تنسيق الرقم
        if bytes_size >= 100:
            return f"{bytes_size:.0f} {units[unit_index]}"
        elif bytes_size >= 10:
            return f"{bytes_size:.1f} {units[unit_index]}"
        else:
            return f"{bytes_size:.2f} {units[unit_index]}"
            
    except (ValueError, TypeError):
        return "0 B"

def format_number(number: Union[int, float], precision: int = 1) -> str:
    """تنسيق الأرقام الكبيرة بوحدات مختصرة"""
    try:
        if not number or number == 0:
            return "0"
        
        number = float(number)
        
        # الوحدات المختصرة
        units = [
            (1_000_000_000_000, 'T'),  # تريليون
            (1_000_000_000, 'B'),      # بليون
            (1_000_000, 'M'),          # مليون
            (1_000, 'K')               # ألف
        ]
        
        for threshold, unit in units:
            if abs(number) >= threshold:
                formatted = number / threshold
                if formatted >= 100:
                    return f"{formatted:.0f}{unit}"
                else:
                    return f"{formatted:.{precision}f}{unit}"
        
        # للأرقام الأصغر من 1000
        if number >= 100:
            return f"{number:.0f}"
        elif number >= 10:
            return f"{number:.1f}"
        else:
            return f"{number:.2f}"
            
    except (ValueError, TypeError):
        return "0"

def format_percentage(value: Union[int, float], total: Union[int, float]) -> str:
    """تنسيق النسبة المئوية"""
    try:
        if not total or total == 0:
            return "0%"
        
        percentage = (float(value) / float(total)) * 100
        
        if percentage >= 99.5:
            return "100%"
        elif percentage >= 10:
            return f"{percentage:.1f}%"
        else:
            return f"{percentage:.2f}%"
            
    except (ValueError, TypeError, ZeroDivisionError):
        return "0%"

def format_time_ago(timestamp: Union[datetime, float, int]) -> str:
    """تنسيق الوقت المنقضي"""
    try:
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        
        now = datetime.now()
        diff = now - timestamp
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return "الآن"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"قبل {minutes} دقيقة" if minutes == 1 else f"قبل {minutes} دقائق"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"قبل {hours} ساعة" if hours == 1 else f"قبل {hours} ساعات"
        elif seconds < 2592000:  # 30 days
            days = seconds // 86400
            return f"قبل {days} يوم" if days == 1 else f"قبل {days} أيام"
        elif seconds < 31536000:  # 365 days
            months = seconds // 2592000
            return f"قبل {months} شهر" if months == 1 else f"قبل {months} أشهر"
        else:
            years = seconds // 31536000
            return f"قبل {years} سنة" if years == 1 else f"قبل {years} سنوات"
            
    except (ValueError, TypeError):
        return "غير معروف"

def convert_bytes(size: float) -> str:
    """تحويل البايتات (نسخة محسنة من الكود الأصلي)"""
    if not size:
        return "0 B"
    
    power = 1024
    n = 0
    power_labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB", 5: "PB"}
    
    while size > power and n < 5:
        size /= power
        n += 1
    
    return f"{size:.2f} {power_labels[n]}"

def get_readable_time(seconds: int) -> str:
    """الحصول على وقت قابل للقراءة (نسخة محسنة)"""
    if not seconds:
        return "0s"
    
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        
        if seconds == 0 and remainder == 0:
            break
            
        time_list.append(int(result))
        seconds = int(remainder)
    
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    
    time_list.reverse()
    ping_time += ":".join(time_list)
    
    return ping_time

def seconds_to_min(seconds: Optional[Union[int, float]]) -> str:
    """تحويل الثواني إلى دقائق وثواني"""
    if seconds is None:
        return "-"
    
    try:
        seconds = int(seconds)
        
        d, h, m, s = (
            seconds // (3600 * 24),
            seconds // 3600 % 24,
            seconds % 3600 // 60,
            seconds % 3600 % 60,
        )
        
        if d > 0:
            return f"{d:02d}:{h:02d}:{m:02d}:{s:02d}"
        elif h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        elif m > 0:
            return f"{m:02d}:{s:02d}"
        elif s > 0:
            return f"00:{s:02d}"
        else:
            return "00:00"
            
    except (ValueError, TypeError):
        return "-"

def time_to_seconds(time_str: str) -> int:
    """تحويل النص الزمني إلى ثواني"""
    try:
        if not time_str or not isinstance(time_str, str):
            return 0
        
        time_str = str(time_str).strip()
        parts = time_str.split(":")
        
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return 0
            
    except (ValueError, TypeError):
        return 0

def speed_converter(seconds: int, speed: Union[str, float]) -> tuple:
    """تحويل السرعة مع حساب الوقت الجديد"""
    try:
        speed = float(speed)
        
        if speed == 0.5:
            new_seconds = int(seconds * 2)
        elif speed == 0.75:
            new_seconds = int(seconds * (4/3))
        elif speed == 1.5:
            new_seconds = int(seconds * (2/3))
        elif speed == 2.0:
            new_seconds = int(seconds * 0.5)
        else:
            new_seconds = seconds
        
        formatted_time = seconds_to_min(new_seconds)
        return formatted_time, new_seconds
        
    except (ValueError, TypeError):
        return seconds_to_min(seconds), seconds

def check_duration(file_path: str) -> Union[float, str]:
    """فحص مدة الملف الصوتي/المرئي"""
    try:
        if not os.path.exists(file_path):
            return "الملف غير موجود"
        
        command = [
            "ffprobe",
            "-loglevel", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return "خطأ في قراءة الملف"
        
        data = json.loads(result.stdout)
        
        # البحث عن المدة في format
        if "format" in data and "duration" in data["format"]:
            return float(data["format"]["duration"])
        
        # البحث عن المدة في streams
        if "streams" in data:
            for stream in data["streams"]:
                if "duration" in stream:
                    return float(stream["duration"])
        
        return "غير معروف"
        
    except subprocess.TimeoutExpired:
        return "انتهت مهلة المعالجة"
    except json.JSONDecodeError:
        return "خطأ في تحليل البيانات"
    except Exception as e:
        return f"خطأ: {str(e)}"

# دوال إضافية متقدمة

def format_bitrate(bitrate: Union[int, float]) -> str:
    """تنسيق معدل البت"""
    try:
        if not bitrate:
            return "غير معروف"
        
        bitrate = int(bitrate)
        
        if bitrate >= 1000:
            return f"{bitrate/1000:.1f} Mbps"
        else:
            return f"{bitrate} kbps"
            
    except (ValueError, TypeError):
        return "غير معروف"

def format_sample_rate(sample_rate: Union[int, float]) -> str:
    """تنسيق معدل العينة"""
    try:
        if not sample_rate:
            return "غير معروف"
        
        sample_rate = int(sample_rate)
        
        if sample_rate >= 1000:
            return f"{sample_rate/1000:.1f} kHz"
        else:
            return f"{sample_rate} Hz"
            
    except (ValueError, TypeError):
        return "غير معروف"

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """إنشاء شريط تقدم نصي"""
    try:
        if not total or total <= 0:
            return "▱" * length
        
        progress = min(current / total, 1.0)
        filled_length = int(length * progress)
        
        bar = "▰" * filled_length + "▱" * (length - filled_length)
        return bar
        
    except (ValueError, TypeError, ZeroDivisionError):
        return "▱" * length

def format_codec_info(codec_name: str, codec_type: str = "") -> str:
    """تنسيق معلومات الكودك"""
    try:
        if not codec_name:
            return "غير معروف"
        
        # تحسين أسماء الكودكات الشائعة
        codec_map = {
            'aac': 'AAC',
            'mp3': 'MP3',
            'opus': 'Opus',
            'vorbis': 'Vorbis',
            'flac': 'FLAC',
            'h264': 'H.264',
            'h265': 'H.265',
            'vp9': 'VP9',
            'av1': 'AV1'
        }
        
        formatted_name = codec_map.get(codec_name.lower(), codec_name.upper())
        
        if codec_type:
            return f"{formatted_name} ({codec_type})"
        else:
            return formatted_name
            
    except Exception:
        return "غير معروف"

# قائمة تنسيقات الفيديو المدعومة
SUPPORTED_VIDEO_FORMATS = [
    "webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng",
    "mov", "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4",
    "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv", "svi", "3gp",
    "3g2", "mxf", "roq", "nsv", "f4v", "f4p", "f4a", "f4b"
]

# قائمة تنسيقات الصوت المدعومة
SUPPORTED_AUDIO_FORMATS = [
    "mp3", "aac", "ogg", "opus", "flac", "wav", "m4a", "wma",
    "aiff", "au", "ra", "3gp", "amr", "ac3", "dts"
]

def is_supported_format(file_path: str, format_type: str = "auto") -> bool:
    """التحقق من دعم تنسيق الملف"""
    try:
        if not file_path:
            return False
        
        extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if format_type == "video":
            return extension in SUPPORTED_VIDEO_FORMATS
        elif format_type == "audio":
            return extension in SUPPORTED_AUDIO_FORMATS
        else:  # auto
            return extension in (SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS)
            
    except Exception:
        return False

# دالة تحميل متقدمة (مبسطة من الكود الأصلي)
def download_chunk(url: str, start: int, end: int, filename: str, session):
    """تحميل جزء من الملف"""
    try:
        headers = {"Range": f"bytes={start}-{end}"}
        response = session.get(url, headers=headers, stream=True, timeout=30)
        
        with open(filename, "ab") as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
    except Exception as e:
        print(f"خطأ في تحميل الجزء {start}-{end}: {e}")

async def int_to_alpha(user_id: int) -> str:
    """تحويل رقم المستخدم إلى أحرف"""
    try:
        alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        text = ""
        user_id = str(user_id)
        
        for digit in user_id:
            if digit.isdigit():
                text += alphabet[int(digit)]
        
        return text
        
    except Exception:
        return "error"

async def alpha_to_int(user_id_alphabet: str) -> int:
    """تحويل الأحرف إلى رقم المستخدم"""
    try:
        alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        user_id = ""
        
        for char in user_id_alphabet:
            if char in alphabet:
                index = alphabet.index(char)
                user_id += str(index)
        
        return int(user_id) if user_id else 0
        
    except Exception:
        return 0