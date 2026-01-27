from telethon import TelegramClient
from telethon.sessions import StringSession

# Default API ID / HASH — bularni sayt settings.py dagi qiymatlar bilan bir xil qoldiryapmiz
api_id = 34259513
api_hash = "558c38cc422e57adf957c21e0062c5fa"

# Bu script faqat raqam, SMS kodi va (bo‘lsa) 2-bosqich parol bilan login qiladi.
# QR KOD KERAK EMAS.
# Oxirida faqat String Session ni chiqaradi.
with TelegramClient(StringSession(), api_id, api_hash) as client:
    # Birinchi ishga tushganda Telethon o‘zi savol beradi:
    #  - Please enter your phone (or bot token):
    #  - Please enter the code you received:
    #  - Please enter your password: (agar 2FA yoqilgan bo‘lsa)
    # Biz bu yerda faqat session stringni chop etamiz.
    print("\n✅ SESSION STRING:\n")
    print(client.session.save())
