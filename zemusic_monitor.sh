#!/bin/bash
# -*- coding: utf-8 -*-
"""
🤖 نظام مراقبة ZeMusic Bot - خدمة 30 يوم
==========================================
يراقب البوت ويعيد تشغيله تلقائياً عند التوقف
مع تسجيل مفصل وإحصائيات شاملة
"""

# إعدادات النظام
BOT_NAME="ZeMusic"
BOT_COMMAND="python3 -m ZeMusic"
LOG_FILE="/tmp/zemusic_monitor.log"
STATS_FILE="/tmp/zemusic_stats.json"
WORKSPACE_DIR="/workspace"
MAX_RESTART_ATTEMPTS=5
RESTART_DELAY=10
HEALTH_CHECK_INTERVAL=30
MONITOR_DURATION=2592000  # 30 يوم بالثواني

# ألوان للعرض
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# دالة التسجيل
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    echo -e "${CYAN}[$timestamp]${NC} ${GREEN}[$level]${NC} $message"
}

# دالة إنشاء ملف الإحصائيات
init_stats() {
    cat > "$STATS_FILE" << EOF
{
    "start_time": "$(date '+%Y-%m-%d %H:%M:%S')",
    "total_restarts": 0,
    "last_restart": "",
    "uptime_hours": 0,
    "health_checks": 0,
    "failed_checks": 0,
    "service_status": "starting",
    "monitor_pid": $$
}
EOF
    log_message "INFO" "📊 تم إنشاء ملف الإحصائيات: $STATS_FILE"
}

# دالة تحديث الإحصائيات
update_stats() {
    local field=$1
    local value=$2
    
    if [[ -f "$STATS_FILE" ]]; then
        # تحديث الحقل المحدد
        python3 -c "
import json
import sys
try:
    with open('$STATS_FILE', 'r') as f:
        stats = json.load(f)
    
    if '$field' == 'total_restarts':
        stats['total_restarts'] += 1
        stats['last_restart'] = '$(date '+%Y-%m-%d %H:%M:%S')'
    elif '$field' == 'health_checks':
        stats['health_checks'] += 1
    elif '$field' == 'failed_checks':
        stats['failed_checks'] += 1
    elif '$field' == 'service_status':
        stats['service_status'] = '$value'
    
    with open('$STATS_FILE', 'w') as f:
        json.dump(stats, f, indent=2)
except Exception as e:
    print(f'Error updating stats: {e}', file=sys.stderr)
"
    fi
}

# دالة فحص حالة البوت
check_bot_status() {
    local bot_pid=$(pgrep -f "$BOT_COMMAND")
    if [[ -n "$bot_pid" ]]; then
        return 0  # البوت يعمل
    else
        return 1  # البوت متوقف
    fi
}

# دالة بدء البوت
start_bot() {
    log_message "INFO" "🚀 بدء تشغيل $BOT_NAME..."
    
    cd "$WORKSPACE_DIR" || {
        log_message "ERROR" "❌ فشل في الانتقال إلى مجلد العمل: $WORKSPACE_DIR"
        return 1
    }
    
    # إيقاف أي عملية سابقة
    pkill -f "$BOT_COMMAND" 2>/dev/null
    sleep 3
    
    # بدء البوت في الخلفية
    nohup $BOT_COMMAND > "/tmp/zemusic_service_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    local bot_pid=$!
    
    # انتظار قصير للتأكد من بدء التشغيل
    sleep 5
    
    if check_bot_status; then
        log_message "SUCCESS" "✅ تم بدء $BOT_NAME بنجاح (PID: $bot_pid)"
        update_stats "service_status" "running"
        return 0
    else
        log_message "ERROR" "❌ فشل في بدء $BOT_NAME"
        update_stats "service_status" "failed"
        return 1
    fi
}

# دالة إعادة تشغيل البوت
restart_bot() {
    local attempt=$1
    log_message "WARNING" "🔄 محاولة إعادة تشغيل $BOT_NAME (المحاولة $attempt/$MAX_RESTART_ATTEMPTS)"
    
    # إيقاف البوت إذا كان يعمل
    pkill -f "$BOT_COMMAND" 2>/dev/null
    sleep 5
    
    # محاولة بدء البوت
    if start_bot; then
        update_stats "total_restarts"
        log_message "SUCCESS" "✅ تم إعادة تشغيل $BOT_NAME بنجاح"
        return 0
    else
        log_message "ERROR" "❌ فشل في إعادة تشغيل $BOT_NAME"
        return 1
    fi
}

# دالة عرض الإحصائيات
show_stats() {
    if [[ -f "$STATS_FILE" ]]; then
        echo -e "\n${PURPLE}📊 إحصائيات خدمة $BOT_NAME${NC}"
        echo -e "${PURPLE}================================${NC}"
        
        python3 -c "
import json
import datetime
try:
    with open('$STATS_FILE', 'r') as f:
        stats = json.load(f)
    
    start_time = datetime.datetime.strptime(stats['start_time'], '%Y-%m-%d %H:%M:%S')
    uptime = datetime.datetime.now() - start_time
    uptime_hours = uptime.total_seconds() / 3600
    
    print(f'🕐 وقت البدء: {stats[\"start_time\"]}')
    print(f'⏱️  وقت التشغيل: {uptime_hours:.1f} ساعة')
    print(f'🔄 إعادة التشغيل: {stats[\"total_restarts\"]} مرة')
    print(f'💓 فحوصات الصحة: {stats[\"health_checks\"]}')
    print(f'❌ فحوصات فاشلة: {stats[\"failed_checks\"]}')
    print(f'📊 حالة الخدمة: {stats[\"service_status\"]}')
    
    if stats['last_restart']:
        print(f'🕐 آخر إعادة تشغيل: {stats[\"last_restart\"]}')
    
    # حساب معدل الاستقرار
    if stats['health_checks'] > 0:
        stability = ((stats['health_checks'] - stats['failed_checks']) / stats['health_checks']) * 100
        print(f'🎯 معدل الاستقرار: {stability:.1f}%')
    
except Exception as e:
    print(f'خطأ في قراءة الإحصائيات: {e}')
"
    fi
}

# دالة التنظيف عند الإنهاء
cleanup() {
    log_message "INFO" "🛑 إيقاف خدمة المراقبة..."
    update_stats "service_status" "stopped"
    
    # عرض الإحصائيات النهائية
    show_stats
    
    log_message "INFO" "📋 ملخص الخدمة:"
    log_message "INFO" "   📁 ملف السجل: $LOG_FILE"
    log_message "INFO" "   📊 ملف الإحصائيات: $STATS_FILE"
    log_message "INFO" "   🕐 مدة الخدمة: 30 يوم"
    
    exit 0
}

# دالة الحلقة الرئيسية للمراقبة
monitor_loop() {
    local start_time=$(date +%s)
    local end_time=$((start_time + MONITOR_DURATION))
    local restart_attempts=0
    
    log_message "INFO" "🎯 بدء مراقبة $BOT_NAME لمدة 30 يوم"
    log_message "INFO" "🔍 فحص كل $HEALTH_CHECK_INTERVAL ثانية"
    
    while [[ $(date +%s) -lt $end_time ]]; do
        update_stats "health_checks"
        
        if check_bot_status; then
            # البوت يعمل بشكل طبيعي
            restart_attempts=0
            update_stats "service_status" "running"
            
            # عرض حالة دورية كل ساعة
            local current_time=$(date +%s)
            local elapsed_hours=$(( (current_time - start_time) / 3600 ))
            
            if (( elapsed_hours % 1 == 0 && (current_time - start_time) % 3600 < HEALTH_CHECK_INTERVAL )); then
                log_message "INFO" "💚 $BOT_NAME يعمل بشكل طبيعي (${elapsed_hours}h)"
                show_stats
            fi
        else
            # البوت متوقف - محاولة إعادة التشغيل
            update_stats "failed_checks"
            update_stats "service_status" "restarting"
            
            restart_attempts=$((restart_attempts + 1))
            
            if [[ $restart_attempts -le $MAX_RESTART_ATTEMPTS ]]; then
                log_message "WARNING" "⚠️  $BOT_NAME متوقف! محاولة إعادة التشغيل..."
                
                if restart_bot $restart_attempts; then
                    restart_attempts=0
                    log_message "SUCCESS" "✅ تم إعادة تشغيل $BOT_NAME بنجاح"
                else
                    log_message "ERROR" "❌ فشل في إعادة التشغيل - انتظار ${RESTART_DELAY}s"
                    sleep $RESTART_DELAY
                fi
            else
                log_message "CRITICAL" "🚨 فشل في إعادة تشغيل $BOT_NAME بعد $MAX_RESTART_ATTEMPTS محاولات"
                log_message "CRITICAL" "🔄 إعادة تعيين العداد والمحاولة مرة أخرى"
                restart_attempts=0
                sleep $((RESTART_DELAY * 2))
            fi
        fi
        
        # انتظار قبل الفحص التالي
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_message "INFO" "⏰ انتهت فترة المراقبة (30 يوم)"
    log_message "INFO" "🎉 تم إكمال الخدمة بنجاح!"
}

# الدالة الرئيسية
main() {
    echo -e "${GREEN}🤖 خدمة مراقبة $BOT_NAME - 30 يوم${NC}"
    echo -e "${GREEN}====================================${NC}"
    echo -e "${YELLOW}📅 بدء الخدمة: $(date)${NC}"
    echo -e "${YELLOW}📅 انتهاء الخدمة: $(date -d '+30 days')${NC}"
    echo -e "${BLUE}📁 مجلد العمل: $WORKSPACE_DIR${NC}"
    echo -e "${BLUE}📝 ملف السجل: $LOG_FILE${NC}"
    echo -e "${BLUE}📊 ملف الإحصائيات: $STATS_FILE${NC}"
    echo ""
    
    # إعداد معالجات الإشارات
    trap cleanup SIGINT SIGTERM EXIT
    
    # تهيئة النظام
    init_stats
    
    # بدء البوت إذا لم يكن يعمل
    if ! check_bot_status; then
        log_message "INFO" "🚀 البوت غير مشغل - بدء التشغيل..."
        start_bot
    else
        log_message "INFO" "✅ البوت يعمل بالفعل"
        update_stats "service_status" "running"
    fi
    
    # بدء حلقة المراقبة
    monitor_loop
}

# تشغيل الدالة الرئيسية
main "$@"