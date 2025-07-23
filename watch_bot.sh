#!/bin/bash
# 🔍 سكريبت مراقبة البوت المبسط

clear
echo "🎵 نظام مراقبة بوت ZeMusic"
echo "================================"
echo ""

while true; do
    # فحص حالة البوت
    BOT_PID=$(pgrep -f 'python.*ZeMusic')
    if [ ! -z "$BOT_PID" ]; then
        echo "✅ البوت يعمل (PID: $BOT_PID)"
        
        # عرض آخر 5 أسطر من السجل
        echo ""
        echo "📋 آخر الأحداث:"
        echo "---------------"
        tail -n 5 bot_runtime.log 2>/dev/null | while IFS= read -r line; do
            echo "  $line"
        done
        
        # عرض إحصائيات سريعة
        echo ""
        echo "📊 إحصائيات سريعة:"
        echo "🖥️ المعالج: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)%"
        echo "🧠 الذاكرة: $(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')%"
        echo "⏰ الوقت: $(date '+%H:%M:%S')"
        
    else
        echo "❌ البوت متوقف!"
        echo "🔄 محاولة إعادة التشغيل..."
        nohup python3 -m ZeMusic > bot_runtime.log 2>&1 &
        sleep 5
    fi
    
    echo ""
    echo "🔄 التحديث كل 10 ثوان... (Ctrl+C للإيقاف)"
    echo "================================"
    sleep 10
    clear
    echo "🎵 نظام مراقبة بوت ZeMusic"
    echo "================================"
    echo ""
done
