#!/bin/bash
# -*- coding: utf-8 -*-
"""
🎛️ أداة التحكم في خدمة ZeMusic Bot
===================================
للتحكم ومراقبة خدمة البوت لمدة 30 يوم
"""

# ألوان للعرض
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ملفات النظام
STATS_FILE="/tmp/zemusic_stats.json"
LOG_FILE="/tmp/zemusic_monitor.log"
PID_FILE="/tmp/zemusic_monitor.pid"
SERVICE_LOG="/tmp/zemusic_30day_service.log"

# دالة عرض الحالة
show_status() {
    echo -e "${GREEN}🤖 حالة خدمة ZeMusic Bot${NC}"
    echo -e "${GREEN}===========================${NC}"
    
    # فحص خدمة المراقبة
    if pgrep -f "zemusic_service.py" > /dev/null; then
        echo -e "${GREEN}✅ خدمة المراقبة: تعمل${NC}"
        MONITOR_PID=$(pgrep -f "zemusic_service.py")
        echo -e "${BLUE}   PID: $MONITOR_PID${NC}"
    else
        echo -e "${RED}❌ خدمة المراقبة: متوقفة${NC}"
    fi
    
    # فحص البوت
    if pgrep -f "python3 -m ZeMusic" > /dev/null; then
        echo -e "${GREEN}✅ ZeMusic Bot: يعمل${NC}"
        BOT_PID=$(pgrep -f "python3 -m ZeMusic")
        echo -e "${BLUE}   PID: $BOT_PID${NC}"
    else
        echo -e "${RED}❌ ZeMusic Bot: متوقف${NC}"
    fi
    
    echo ""
}

# دالة عرض الإحصائيات
show_stats() {
    echo -e "${PURPLE}📊 إحصائيات الخدمة${NC}"
    echo -e "${PURPLE}==================${NC}"
    
    if [[ -f "$STATS_FILE" ]]; then
        python3 -c "
import json
import datetime
try:
    with open('$STATS_FILE', 'r') as f:
        stats = json.load(f)
    
    start_time = datetime.datetime.fromisoformat(stats['start_time'])
    uptime = datetime.datetime.now() - start_time
    uptime_hours = uptime.total_seconds() / 3600
    
    print(f'🕐 وقت البدء: {start_time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print(f'⏱️  وقت التشغيل: {uptime_hours:.1f} ساعة')
    print(f'🔄 إعادة التشغيل: {stats[\"total_restarts\"]} مرة')
    print(f'✅ نجح: {stats[\"successful_restarts\"]} | ❌ فشل: {stats[\"failed_restarts\"]}')
    print(f'💓 فحوصات الصحة: {stats[\"health_checks\"]}')
    print(f'❌ فحوصات فاشلة: {stats[\"failed_checks\"]}')
    print(f'📊 حالة الخدمة: {stats[\"service_status\"]}')
    
    if stats['last_restart']:
        last_restart = datetime.datetime.fromisoformat(stats['last_restart'])
        print(f'🕐 آخر إعادة تشغيل: {last_restart.strftime(\"%Y-%m-%d %H:%M:%S\")}')
    
    # حساب معدل الاستقرار
    if stats['health_checks'] > 0:
        stability = ((stats['health_checks'] - stats['failed_checks']) / stats['health_checks']) * 100
        print(f'🎯 معدل الاستقرار: {stability:.1f}%')
    
    # حساب الوقت المتبقي
    service_duration = 30 * 24 * 3600  # 30 يوم
    remaining_seconds = service_duration - uptime.total_seconds()
    remaining_days = remaining_seconds / (24 * 3600)
    
    if remaining_days > 0:
        print(f'⏳ الوقت المتبقي: {remaining_days:.1f} يوم')
    else:
        print('✅ تم إكمال فترة الخدمة')

except Exception as e:
    print(f'خطأ في قراءة الإحصائيات: {e}')
"
    else
        echo -e "${RED}❌ ملف الإحصائيات غير موجود${NC}"
    fi
    echo ""
}

# دالة عرض السجل
show_logs() {
    local lines=${1:-20}
    echo -e "${CYAN}📝 آخر $lines سطر من السجل${NC}"
    echo -e "${CYAN}========================${NC}"
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo -e "${RED}❌ ملف السجل غير موجود${NC}"
    fi
    echo ""
}

# دالة المراقبة المباشرة
live_monitor() {
    echo -e "${YELLOW}🔍 مراقبة مباشرة للسجل (اضغط Ctrl+C للخروج)${NC}"
    echo -e "${YELLOW}============================================${NC}"
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}❌ ملف السجل غير موجود${NC}"
    fi
}

# دالة إعادة تشغيل الخدمة
restart_service() {
    echo -e "${YELLOW}🔄 إعادة تشغيل خدمة المراقبة...${NC}"
    
    # إيقاف الخدمة الحالية
    pkill -f "zemusic_service.py" 2>/dev/null
    sleep 3
    
    # بدء خدمة جديدة
    cd /workspace
    nohup python3 zemusic_service.py > /tmp/zemusic_30day_service.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "zemusic_service.py" > /dev/null; then
        echo -e "${GREEN}✅ تم إعادة تشغيل الخدمة بنجاح${NC}"
    else
        echo -e "${RED}❌ فشل في إعادة تشغيل الخدمة${NC}"
    fi
}

# دالة إيقاف الخدمة
stop_service() {
    echo -e "${RED}🛑 إيقاف خدمة المراقبة...${NC}"
    
    pkill -f "zemusic_service.py" 2>/dev/null
    pkill -f "python3 -m ZeMusic" 2>/dev/null
    
    sleep 3
    
    if ! pgrep -f "zemusic_service.py" > /dev/null; then
        echo -e "${GREEN}✅ تم إيقاف الخدمة${NC}"
    else
        echo -e "${RED}❌ فشل في إيقاف الخدمة${NC}"
    fi
}

# دالة عرض المساعدة
show_help() {
    echo -e "${BLUE}🎛️  أداة التحكم في خدمة ZeMusic Bot${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo ""
    echo -e "${GREEN}الأوامر المتاحة:${NC}"
    echo -e "  ${YELLOW}status${NC}     - عرض حالة الخدمة والبوت"
    echo -e "  ${YELLOW}stats${NC}      - عرض الإحصائيات التفصيلية"
    echo -e "  ${YELLOW}logs [n]${NC}   - عرض آخر n سطر من السجل (افتراضي: 20)"
    echo -e "  ${YELLOW}monitor${NC}    - مراقبة السجل مباشرة"
    echo -e "  ${YELLOW}restart${NC}    - إعادة تشغيل خدمة المراقبة"
    echo -e "  ${YELLOW}stop${NC}       - إيقاف الخدمة نهائياً"
    echo -e "  ${YELLOW}help${NC}       - عرض هذه المساعدة"
    echo ""
    echo -e "${GREEN}أمثلة:${NC}"
    echo -e "  ${CYAN}./service_control.sh status${NC}     # عرض الحالة"
    echo -e "  ${CYAN}./service_control.sh logs 50${NC}    # عرض آخر 50 سطر"
    echo -e "  ${CYAN}./service_control.sh monitor${NC}    # مراقبة مباشرة"
    echo ""
}

# الدالة الرئيسية
main() {
    case "${1:-help}" in
        "status")
            show_status
            ;;
        "stats")
            show_stats
            ;;
        "logs")
            show_logs "${2:-20}"
            ;;
        "monitor")
            live_monitor
            ;;
        "restart")
            restart_service
            ;;
        "stop")
            stop_service
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# تشغيل الدالة الرئيسية
main "$@"