# -*- coding: utf-8 -*-
"""
أدوات Git مبسطة مع Telethon
"""

import asyncio
import shlex
import subprocess
from typing import Tuple

import config
from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    """تشغيل أمر shell وإرجاع النتائج"""
    async def install_requirements():
        try:
            args = shlex.split(cmd)
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            return (
                stdout.decode("utf-8", "replace").strip(),
                stderr.decode("utf-8", "replace").strip(),
                process.returncode,
                process.pid,
            )
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تشغيل الأمر: {e}")
            return ("", str(e), 1, 0)

    return asyncio.get_event_loop().run_until_complete(install_requirements())


async def get_git_info():
    """الحصول على معلومات Git (إذا كانت متاحة)"""
    try:
        # محاولة الحصول على معلومات Git
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            
            # محاولة الحصول على الفرع
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            return {
                'commit': commit_hash,
                'branch': branch,
                'available': True
            }
        else:
            return {
                'commit': 'unknown',
                'branch': 'unknown',
                'available': False
            }
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        LOGGER(__name__).warning(f"Git غير متاح: {e}")
        return {
            'commit': 'unknown',
            'branch': 'unknown',
            'available': False
        }


async def update_requirements():
    """تحديث المتطلبات"""
    try:
        cmd = "pip install -r requirements.txt --upgrade"
        result = install_req(cmd)
        
        if result[2] == 0:  # return code
            return True, result[0]
        else:
            return False, result[1]
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في تحديث المتطلبات: {e}")
        return False, str(e)


async def get_version_info():
    """الحصول على معلومات النسخة"""
    try:
        git_info = await get_git_info()
        
        version_info = {
            'bot_version': config.BOT_VERSION if hasattr(config, 'BOT_VERSION') else '1.0.0',
            'git_commit': git_info['commit'],
            'git_branch': git_info['branch'],
            'git_available': git_info['available']
        }
        
        return version_info
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في الحصول على معلومات النسخة: {e}")
        return {
            'bot_version': '1.0.0',
            'git_commit': 'unknown',
            'git_branch': 'unknown',
            'git_available': False
        }
