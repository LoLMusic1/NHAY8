#!/bin/bash
echo "🔍 مراقبة البوت ZeMusic"
echo "======================="

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if pgrep -f "python3 -m ZeMusic" > /dev/null; then
        pid=$(pgrep -f "python3 -m ZeMusic")
        cpu=$(ps -p $pid -o %cpu --no-headers 2>/dev/null | tr -d ' ')
        mem=$(ps -p $pid -o %mem --no-headers 2>/dev/null | tr -d ' ')
        echo "[$timestamp] 🟢 البوت يعمل | PID: $pid | CPU: ${cpu}% | Memory: ${mem}%"
    else
        echo "[$timestamp] 🔴 البوت متوقف!"
    fi
    
    sleep 10
done
