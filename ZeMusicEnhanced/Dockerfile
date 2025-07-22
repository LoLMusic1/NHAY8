# 🎵 ZeMusic Bot v3.0 - Enhanced Docker Configuration
# تاريخ الإنشاء: 2025-01-28
# النسخة: 3.0.0 - Enhanced Edition

# ============================================
# المرحلة الأساسية
# ============================================

FROM python:3.11-slim-bookworm

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    DEBIAN_FRONTEND=noninteractive

# إنشاء مستخدم غير جذر للأمان
RUN groupadd --gid 1000 zemusic && \
    useradd --uid 1000 --gid zemusic --shell /bin/bash --create-home zemusic

# تحديث النظام وتثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    # أدوات النظام الأساسية
    curl \
    wget \
    git \
    unzip \
    ca-certificates \
    # مكتبات الصوت والفيديو
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    # مكتبات Python الأساسية
    python3-dev \
    python3-pip \
    build-essential \
    gcc \
    g++ \
    # مكتبات الشبكة والأمان
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    # مكتبات الصور
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    # مكتبات قاعدة البيانات
    libsqlite3-dev \
    libpq-dev \
    # أدوات المراقبة
    htop \
    neofetch \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# ترقية pip وتثبيت الأدوات الأساسية
RUN pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات أولاً (للاستفادة من Docker cache)
COPY requirements.txt .

# تثبيت متطلبات Python
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# ============================================
# مرحلة التطبيق
# ============================================

# نسخ ملفات التطبيق
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p \
    logs \
    downloads \
    temp \
    sessions \
    backups \
    cookies \
    assets \
    && chown -R zemusic:zemusic /app

# تعيين الصلاحيات
RUN chmod +x start.sh 2>/dev/null || echo "start.sh not found, skipping..."

# التبديل للمستخدم غير الجذر
USER zemusic

# ============================================
# إعدادات الصحة والمراقبة
# ============================================

# فحص صحة التطبيق
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# تعيين المنافذ المكشوفة
EXPOSE 8000

# متغيرات البيئة الافتراضية
ENV LOG_LEVEL=INFO \
    HIGH_LOAD_MODE=True \
    AUTO_BACKUP=True \
    ENABLE_DATABASE_CACHE=True

# ملصقات Docker
LABEL maintainer="ZeMusic Team" \
      version="3.0.0" \
      description="ZeMusic Bot Enhanced - High Performance Telegram Music Bot" \
      org.opencontainers.image.title="ZeMusic Bot Enhanced" \
      org.opencontainers.image.description="Advanced Telegram Music Bot with Telethon" \
      org.opencontainers.image.version="3.0.0" \
      org.opencontainers.image.created="2025-01-28" \
      org.opencontainers.image.source="https://github.com/your-username/ZeMusic-Enhanced" \
      org.opencontainers.image.licenses="MIT"

# ============================================
# أوامر التشغيل
# ============================================

# الأمر الافتراضي
CMD ["python", "-m", "ZeMusicEnhanced"]

# أمر بديل للتطوير
# CMD ["python", "-m", "ZeMusicEnhanced", "--debug"]