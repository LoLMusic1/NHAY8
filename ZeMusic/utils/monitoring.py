"""
وحدة المراقبة البسيطة
"""

from ZeMusic.logging import LOGGER
import time

def log_info(message):
    """تسجيل رسالة معلومات"""
    LOGGER(__name__).info(message)

def log_error(message):
    """تسجيل رسالة خطأ"""
    LOGGER(__name__).error(message)

class PerformanceMonitor:
    """مراقب الأداء البسيط"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_uptime(self):
        """الحصول على وقت التشغيل"""
        return time.time() - self.start_time
        
    def log_performance(self, operation, duration):
        """تسجيل أداء العملية"""
        LOGGER(__name__).info(f"🔍 {operation}: {duration:.2f}s")

# دوال أخرى للمراقبة
async def monitor_system():
    """مراقبة النظام"""
    pass

async def track_performance():
    """تتبع الأداء"""
    pass
