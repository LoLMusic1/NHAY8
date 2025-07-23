#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار إرسال الملفات الصوتية
"""

import asyncio
import os
from telethon.tl.types import DocumentAttributeAudio

async def test_send_audio(message, file_path: str, title: str = "اختبار"):
    """اختبار إرسال ملف صوتي"""
    try:
        print(f"🧪 اختبار إرسال: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ الملف غير موجود: {file_path}")
            return False
        
        # إرسال الملف
        audio_message = await message.reply(
            file=file_path,
            message=f"🎵 **{title}**\n🧪 **اختبار إرسال**\n🤖 **بواسطة:** ZeMusic Bot",
            attributes=[
                DocumentAttributeAudio(
                    duration=180,  # 3 دقائق افتراضي
                    title=title,
                    performer="ZeMusic Bot"
                )
            ]
        )
        
        print(f"✅ تم إرسال الملف بنجاح: {audio_message.id}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إرسال الملف: {e}")
        return False

if __name__ == "__main__":
    print("🧪 اختبار إرسال الملفات الصوتية")