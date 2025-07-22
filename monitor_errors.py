#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 مراقب الأخطاء في الوقت الفعلي
=========================

مراقبة شاملة لجميع الأخطاء والتحذيرات
"""

import asyncio
import time
import re
from datetime import datetime
from pathlib import Path

class ErrorMonitor:
    def __init__(self, log_file="bot_monitoring.log"):
        self.log_file = Path(log_file)
        self.last_position = 0
        self.error_count = 0
        self.warning_count = 0
        self.start_time = datetime.now()
        
        # أنماط الأخطاء المختلفة
        self.error_patterns = {
            'ERROR': r'\[.*? - ERROR\] - (.*)',
            'WARNING': r'\[.*? - WARNING\] - (.*)',
            'CRITICAL': r'\[.*? - CRITICAL\] - (.*)',
            'Exception': r'(.*Exception.*)',
            'Traceback': r'(Traceback.*)',
            'Failed': r'.*(failed|فشل|خطأ).*',
        }
    
    def monitor_logs(self):
        """مراقبة السجلات الجديدة"""
        if not self.log_file.exists():
            print("❌ ملف السجل غير موجود")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # الذهاب للموضع الأخير
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                for line in new_lines:
                    self.analyze_line(line.strip())
                    
        except Exception as e:
            print(f"❌ خطأ في قراءة السجل: {e}")
    
    def analyze_line(self, line):
        """تحليل سطر واحد من السجل"""
        if not line:
            return
        
        # تحديد نوع الرسالة
        for pattern_name, pattern in self.error_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                self.handle_error(pattern_name, line)
                break
        else:
            # رسالة عادية - عرض INFO فقط
            if "INFO" in line and any(keyword in line for keyword in ["تم", "نجح", "✅", "🚀"]):
                print(f"✅ {self.extract_log_message(line)}")
    
    def handle_error(self, error_type, line):
        """معالجة الأخطاء المكتشفة"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = self.extract_log_message(line)
        
        if error_type == "ERROR":
            self.error_count += 1
            print(f"🔴 [{timestamp}] خطأ #{self.error_count}: {message}")
            self.suggest_solution(message)
            
        elif error_type == "WARNING":
            self.warning_count += 1
            print(f"🟡 [{timestamp}] تحذير #{self.warning_count}: {message}")
            
        elif error_type == "CRITICAL":
            print(f"🚨 [{timestamp}] خطأ حرج: {message}")
            
        elif "Exception" in error_type:
            self.error_count += 1
            print(f"💥 [{timestamp}] استثناء #{self.error_count}: {message}")
            
        elif "Failed" in error_type:
            print(f"❌ [{timestamp}] فشل: {message}")
    
    def extract_log_message(self, line):
        """استخراج الرسالة من سطر السجل"""
        # إزالة الطابع الزمني ومستوى السجل
        parts = line.split(" - ", 3)
        if len(parts) >= 4:
            return parts[3]
        return line
    
    def suggest_solution(self, error_message):
        """اقتراح حلول للأخطاء الشائعة"""
        suggestions = {
            "timeout": "💡 جرب زيادة مهلة الانتظار",
            "connection": "💡 تحقق من الاتصال بالإنترنت",
            "cookies": "💡 قم بتحديث ملفات الكوكيز", 
            "file not found": "💡 تأكد من وجود الملف",
            "permission": "💡 تحقق من الصلاحيات",
            "api": "💡 تحقق من مفاتيح API",
            "database": "💡 تحقق من قاعدة البيانات",
        }
        
        error_lower = error_message.lower()
        for keyword, suggestion in suggestions.items():
            if keyword in error_lower:
                print(f"   {suggestion}")
                break
    
    def print_status(self):
        """طباعة حالة المراقبة"""
        runtime = datetime.now() - self.start_time
        print(f"\n📊 حالة المراقبة:")
        print(f"⏱️  وقت التشغيل: {runtime}")
        print(f"🔴 أخطاء: {self.error_count}")
        print(f"🟡 تحذيرات: {self.warning_count}")
        print(f"📁 حجم السجل: {self.log_file.stat().st_size if self.log_file.exists() else 0} بايت")
        print("-" * 50)

def main():
    monitor = ErrorMonitor()
    
    print("🔍 بدء مراقبة الأخطاء في الوقت الفعلي...")
    print("📝 ملف السجل: bot_monitoring.log")
    print("⚡ سيتم عرض الأخطاء والتحذيرات فور حدوثها")
    print("🛑 اضغط Ctrl+C للتوقف")
    print("=" * 50)
    
    try:
        while True:
            monitor.monitor_logs()
            time.sleep(1)  # فحص كل ثانية
            
            # طباعة حالة دورية
            if int(time.time()) % 30 == 0:  # كل 30 ثانية
                monitor.print_status()
                
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف المراقبة")
        monitor.print_status()
        print("\n📋 ملخص الجلسة:")
        if monitor.error_count == 0 and monitor.warning_count == 0:
            print("✅ لم يتم اكتشاف أي أخطاء!")
        else:
            print(f"🔴 إجمالي الأخطاء: {monitor.error_count}")
            print(f"🟡 إجمالي التحذيرات: {monitor.warning_count}")

if __name__ == "__main__":
    main()