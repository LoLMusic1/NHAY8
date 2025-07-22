#!/bin/bash

# 🎵 ZeMusic Bot v3.0 - Enhanced Startup Script
# تاريخ الإنشاء: 2025-01-28
# النسخة: 3.0.0 - Enhanced Edition

set -e  # إيقاف السكريبت عند أول خطأ

# ============================================
# الألوان والرموز
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# الرموز
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
MUSIC="🎵"
ROBOT="🤖"

# ============================================
# الوظائف المساعدة
# ============================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║       🎵 ZeMusic Bot v3.0 - Enhanced Edition 🎵         ║"
    echo "║                                                          ║"
    echo "║  🚀 بوت الموسيقى الأكثر تطوراً على تيليجرام           ║"
    echo "║  📊 مُحسن للعمل مع 7000 مجموعة و 70000 مستخدم         ║"
    echo "║  ⚡ مدعوم بـ Telethon للأداء الفائق                    ║"
    echo "║                                                          ║"
    echo "║  تاريخ الإنشاء: 2025-01-28                              ║"
    echo "║  النسخة: 3.0.0 - Enhanced Edition                      ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[${timestamp}] ${INFO} ${message}${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] ${WARNING} ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ${ERROR} ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] ${SUCCESS} ${message}${NC}"
            ;;
        *)
            echo -e "${WHITE}[${timestamp}] ${message}${NC}"
            ;;
    esac
}

check_requirements() {
    log "INFO" "فحص المتطلبات الأساسية..."
    
    # فحص Python
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 غير مثبت!"
        return 1
    fi
    
    # فحص نسخة Python
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        log "ERROR" "Python 3.8+ مطلوب! النسخة الحالية: $python_version"
        return 1
    fi
    
    # فحص pip
    if ! command -v pip3 &> /dev/null; then
        log "ERROR" "pip3 غير مثبت!"
        return 1
    fi
    
    # فحص FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log "WARN" "FFmpeg غير مثبت - قد يؤثر على تشغيل الموسيقى"
    fi
    
    # فحص Git
    if ! command -v git &> /dev/null; then
        log "WARN" "Git غير مثبت - لن تعمل ميزات التحديث التلقائي"
    fi
    
    log "SUCCESS" "تم فحص المتطلبات بنجاح"
    return 0
}

setup_environment() {
    log "INFO" "إعداد البيئة..."
    
    # إنشاء المجلدات المطلوبة
    local directories=(
        "logs"
        "downloads"
        "temp"
        "sessions"
        "backups"
        "cookies"
        "assets"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "INFO" "تم إنشاء مجلد: $dir"
        fi
    done
    
    # فحص ملف البيئة
    if [ ! -f ".env" ]; then
        if [ -f "sample.env" ]; then
            log "WARN" "ملف .env غير موجود - سيتم نسخ sample.env"
            cp sample.env .env
            log "INFO" "تم إنشاء ملف .env - يرجى تعديل الإعدادات المطلوبة"
        else
            log "ERROR" "ملف sample.env غير موجود!"
            return 1
        fi
    fi
    
    log "SUCCESS" "تم إعداد البيئة بنجاح"
    return 0
}

install_requirements() {
    log "INFO" "تثبيت المتطلبات..."
    
    # ترقية pip
    python3 -m pip install --upgrade pip
    
    # تثبيت المتطلبات
    if [ -f "requirements.txt" ]; then
        log "INFO" "تثبيت المتطلبات من requirements.txt..."
        python3 -m pip install -r requirements.txt --upgrade
    else
        log "ERROR" "ملف requirements.txt غير موجود!"
        return 1
    fi
    
    log "SUCCESS" "تم تثبيت المتطلبات بنجاح"
    return 0
}

check_config() {
    log "INFO" "فحص ملف الإعدادات..."
    
    # التحقق من وجود المتغيرات المطلوبة
    source .env 2>/dev/null || true
    
    local required_vars=(
        "API_ID"
        "API_HASH"
        "BOT_TOKEN"
        "OWNER_ID"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log "ERROR" "المتغيرات التالية مطلوبة في ملف .env:"
        for var in "${missing_vars[@]}"; do
            echo -e "${RED}  - $var${NC}"
        done
        log "INFO" "يرجى تعديل ملف .env وإضافة القيم المطلوبة"
        return 1
    fi
    
    log "SUCCESS" "ملف الإعدادات صحيح"
    return 0
}

cleanup_old_files() {
    log "INFO" "تنظيف الملفات القديمة..."
    
    # تنظيف ملفات Python المؤقتة
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # تنظيف الملفات المؤقتة
    if [ -d "temp" ]; then
        rm -rf temp/*
    fi
    
    # تنظيف السجلات القديمة (الاحتفاظ بآخر 10 ملفات)
    if [ -d "logs" ]; then
        ls -t logs/*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    fi
    
    log "SUCCESS" "تم تنظيف الملفات القديمة"
}

show_system_info() {
    log "INFO" "معلومات النظام:"
    echo -e "${BLUE}"
    echo "  💻 النظام: $(uname -s) $(uname -r)"
    echo "  🏗️  المعمارية: $(uname -m)"
    echo "  🐍 Python: $(python3 --version)"
    echo "  📦 pip: $(pip3 --version | cut -d' ' -f2)"
    
    if command -v ffmpeg &> /dev/null; then
        echo "  🎵 FFmpeg: $(ffmpeg -version | head -n1 | cut -d' ' -f3)"
    else
        echo "  🎵 FFmpeg: غير مثبت"
    fi
    
    if command -v git &> /dev/null; then
        echo "  🔄 Git: $(git --version | cut -d' ' -f3)"
    else
        echo "  🔄 Git: غير مثبت"
    fi
    
    echo "  💾 المساحة المتاحة: $(df -h . | awk 'NR==2{print $4}')"
    echo "  🧠 الذاكرة المتاحة: $(free -h | awk 'NR==2{print $7}')"
    echo -e "${NC}"
}

start_bot() {
    log "INFO" "بدء تشغيل ZeMusic Bot Enhanced..."
    
    # تعيين متغيرات البيئة
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    export PYTHONUNBUFFERED=1
    export PYTHONIOENCODING=utf-8
    
    # بدء البوت
    python3 -m ZeMusicEnhanced
}

# ============================================
# معالج الإشارات
# ============================================
cleanup_on_exit() {
    log "INFO" "تنظيف الموارد..."
    # قتل العمليات التابعة
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup_on_exit SIGINT SIGTERM

# ============================================
# الوظيفة الرئيسية
# ============================================
main() {
    # طباعة البانر
    print_banner
    
    # فحص المعاملات
    case "${1:-}" in
        "--install-only")
            log "INFO" "وضع التثبيت فقط"
            check_requirements || exit 1
            setup_environment || exit 1
            install_requirements || exit 1
            log "SUCCESS" "تم التثبيت بنجاح!"
            exit 0
            ;;
        "--check-only")
            log "INFO" "وضع الفحص فقط"
            check_requirements || exit 1
            check_config || exit 1
            show_system_info
            log "SUCCESS" "جميع الفحوصات مرت بنجاح!"
            exit 0
            ;;
        "--help"|"-h")
            echo -e "${WHITE}"
            echo "الاستخدام: $0 [خيارات]"
            echo ""
            echo "الخيارات:"
            echo "  --install-only    تثبيت المتطلبات فقط"
            echo "  --check-only      فحص النظام فقط"
            echo "  --no-cleanup      عدم تنظيف الملفات القديمة"
            echo "  --help, -h        عرض هذه المساعدة"
            echo ""
            echo "بدون خيارات: تشغيل البوت مع الفحص والإعداد الكامل"
            echo -e "${NC}"
            exit 0
            ;;
    esac
    
    # الفحوصات الأساسية
    log "INFO" "بدء فحوصات ما قبل التشغيل..."
    
    check_requirements || {
        log "ERROR" "فشل في فحص المتطلبات"
        exit 1
    }
    
    setup_environment || {
        log "ERROR" "فشل في إعداد البيئة"
        exit 1
    }
    
    check_config || {
        log "ERROR" "فشل في فحص الإعدادات"
        exit 1
    }
    
    # تنظيف الملفات القديمة (إلا إذا تم تعطيله)
    if [[ "$*" != *"--no-cleanup"* ]]; then
        cleanup_old_files
    fi
    
    # عرض معلومات النظام
    show_system_info
    
    # تثبيت المتطلبات
    install_requirements || {
        log "ERROR" "فشل في تثبيت المتطلبات"
        exit 1
    }
    
    log "SUCCESS" "جميع الفحوصات مرت بنجاح!"
    echo ""
    
    # بدء البوت
    start_bot
}

# تشغيل الوظيفة الرئيسية
main "$@"