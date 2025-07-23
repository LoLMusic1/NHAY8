#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 نظام مراقبة البوت المتقدم
==========================
يراقب أداء البوت في الوقت الفعلي ويقدم تقارير مفصلة
"""

import asyncio
import psutil
import time
import os
import sys
from datetime import datetime, timedelta
import json
import subprocess

class BotMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.bot_process = None
        self.stats = {
            'uptime': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'network_io': {'sent': 0, 'recv': 0},
            'errors': 0,
            'warnings': 0,
            'info_messages': 0
        }
        self.log_file = 'bot_runtime.log'
        
    def find_bot_process(self):
        """البحث عن عملية البوت"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'ZeMusic' in ' '.join(proc.info['cmdline']):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def get_system_stats(self):
        """الحصول على إحصائيات النظام"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        self.stats.update({
            'uptime': time.time() - self.start_time,
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'disk_usage': disk.percent,
            'network_io': {
                'sent': network.bytes_sent,
                'recv': network.bytes_recv
            }
        })
        
        bot_proc = self.find_bot_process()
        if bot_proc:
            try:
                self.stats['bot_cpu'] = bot_proc.cpu_percent()
                self.stats['bot_memory'] = bot_proc.memory_info().rss / 1024 / 1024
                self.stats['bot_status'] = 'running'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.stats['bot_status'] = 'not_found'
        else:
            self.stats['bot_status'] = 'stopped'
    
    def analyze_logs(self):
        """تحليل سجلات البوت"""
        if not os.path.exists(self.log_file):
            return
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            recent_lines = lines[-100:]
            
            errors = sum(1 for line in recent_lines if 'ERROR' in line)
            warnings = sum(1 for line in recent_lines if 'WARNING' in line)
            info_messages = sum(1 for line in recent_lines if 'INFO' in line)
            
            self.stats.update({
                'errors': errors,
                'warnings': warnings,
                'info_messages': info_messages,
                'total_log_lines': len(lines)
            })
            
        except Exception as e:
            print(f"خطأ في تحليل السجلات: {e}")
    
    def format_uptime(self, seconds):
        """تنسيق وقت التشغيل"""
        td = timedelta(seconds=int(seconds))
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}د {hours}س {minutes}ق {seconds}ث"
        elif hours > 0:
            return f"{hours}ס {minutes}ق {seconds}ث"
        else:
            return f"{minutes}ق {seconds}ث"
    
    def format_bytes(self, bytes_val):
        """تنسيق البايتات"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"
    
    def print_status(self):
        """طباعة حالة البوت"""
        self.get_system_stats()
        self.analyze_logs()
        
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🎵 " + "="*60)
        print("🔍 نظام مراقبة بوت ZeMusic المتقدم")
        print("="*64)
        print(f"📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ مدة التشغيل: {self.format_uptime(self.stats['uptime'])}")
        print()
        
        status_emoji = "🟢" if self.stats['bot_status'] == 'running' else "🔴"
        print(f"🤖 حالة البوت: {status_emoji} {self.stats['bot_status']}")
        
        if self.stats['bot_status'] == 'running':
            print(f"💾 ذاكرة البوت: {self.stats.get('bot_memory', 0):.1f} MB")
            print(f"⚡ معالج البوت: {self.stats.get('bot_cpu', 0):.1f}%")
        print()
        
        print("📊 إحصائيات النظام:")
        print(f"🖥️  المعالج: {self.stats['cpu_usage']:.1f}%")
        print(f"🧠 الذاكرة: {self.stats['memory_usage']:.1f}%")
        print(f"💿 القرص: {self.stats['disk_usage']:.1f}%")
        print()
        
        print("🌐 الشبكة:")
        print(f"📤 مُرسل: {self.format_bytes(self.stats['network_io']['sent'])}")
        print(f"📥 مُستقبل: {self.format_bytes(self.stats['network_io']['recv'])}")
        print()
        
        print("📝 السجلات:")
        print(f"❌ أخطاء: {self.stats['errors']}")
        print(f"⚠️  تحذيرات: {self.stats['warnings']}")
        print(f"ℹ️  معلومات: {self.stats['info_messages']}")
        print(f"📄 إجمالي الأسطر: {self.stats.get('total_log_lines', 0)}")
        print()
        
        print("📋 آخر الأحداث:")
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-5:]
                    for line in recent_lines:
                        if line.strip():
                            display_line = line.strip()
                            if len(display_line) > 80:
                                display_line = display_line[:77] + "..."
                            print(f"  {display_line}")
            except Exception as e:
                print(f"  خطأ في قراءة السجل: {e}")
        else:
            print("  📭 لا توجد سجلات متاحة")
        
        print()
        print("🔄 التحديث كل 5 ثوان... (Ctrl+C للإيقاف)")
        print("="*64)
    
    async def monitor_loop(self):
        """حلقة المراقبة الرئيسية"""
        try:
            while True:
                self.print_status()
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\n\n🛑 تم إيقاف المراقبة بواسطة المستخدم")
            return

async def main():
    """الدالة الرئيسية"""
    monitor = BotMonitor()
    
    print("🚀 بدء نظام مراقبة البوت...")
    print("⏳ انتظار تحميل البيانات...")
    await asyncio.sleep(2)
    
    await monitor.monitor_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 تم إنهاء البرنامج")
