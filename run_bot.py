#!/usr/bin/env python
"""
Telegram botni ishga tushirish scripti
Ishlatish: python run_bot.py
"""
import os
import sys
import django
import asyncio

# Django sozlamalarini yuklash
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from telegram_app.bot_service import build_application, daily_sender_loop


async def main():
    """Bot va kunlik yuboruvchini ishga tushirish"""
    print("🤖 Telegram bot ishga tushmoqda...")

    application = build_application()

    # Botni initialize qilish
    await application.initialize()
    await application.start()

    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("📱 Bot buyruqlari:")
    print("   /start - Botni sinash")
    print("   /export 1 - Bugungi yuklar")
    print("   /export 7 - 7 kunlik yuklar")
    print("\n⏰ Har kuni soat 00:05 da avtomatik export yuboriladi")
    print("⚠️  To'xtatish uchun: Ctrl+C\n")

    # Polling rejimida ishlash
    await application.updater.start_polling()

    # Kunlik yuboruvchini background da ishga tushirish
    daily_task = asyncio.create_task(
        daily_sender_loop(application, hour=0, minute=5)
    )

    try:
        # Bot ishlashda davom etadi
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n⏹️  Bot to'xtatilmoqda...")
    finally:
        daily_task.cancel()
        await application.stop()
        await application.shutdown()
        print("✅ Bot to'xtatildi")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Xayr!")