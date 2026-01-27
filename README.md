Content is user-generated and unverified.
1
🚚 TG Yuk Monitor
Telegram'dagi yuk e'lonlari kanallaridan ma'lumot olib, ularni bir joyda ko'rsatadigan web-panel.
Loyiha Django + Telethon yordamida ishlaydi.

✨ Yangi Xususiyatlar
🔍 Barcha sahifalarda qidiruv funksiyasi qo'shildi:
Kanallar sahifasi - Kanal nomini qidirish
Xabarlar sahifasi - Matn, kanal, sana bo'yicha qidirish
Statistika sahifasi - Yo'nalish, yuk turi bo'yicha qidirish
Telefonlar sahifasi - Telefon raqam bo'yicha qidirish
Telefon xabarlari - Konkret telefon uchun xabarlarni qidirish
📋 Asosiy Imkoniyatlar
✅ Telegram akkauntingiz bilan telefon raqam orqali login
✅ Kanallar ro'yxatini ko'rish va kerakli kanaldan xabarlarni yuklash
✅ Xabarlardan yo'nalish (A→B), yuk turi, transport, to'lov va telefonlarni avtomatik ajratib olish
✅ Qidiruv funksiyasi barcha sahifalarda
✅ Statistikalar va filtrlar
✅ Excel eksport
✅ Telefonlar ro'yxati va ularning xabarlari
✅ Paginatsiya (har sahifada 20 ta yozuv)
1. Talablar
Python 3.10+ (tavsiya)
Git
Telegram'da developer akkaunt (API ID / API HASH uchun)
2. O'rnatish
bash
git clone https://github.com/Salohiddin08/logistic_tracker.git
cd logistic_tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
3. Sozlamalar
3.1. .env fayl
Loyiha ildizida .env fayl yarating:

SECRET_KEY=ozingizning_django_secret_key_i
DEBUG=True

TG_API_ID=34259513
TG_API_HASH=558c38cc422e57adf957c21e0062c5fa
3.2. Migratsiyalar
bash
python manage.py migrate
python manage.py createsuperuser  # Admin panel uchun
4. Ishga tushirish
bash
python manage.py runserver
Brauzerda oching:

http://127.0.0.1:8000/ – Login
http://127.0.0.1:8000/channels/ – Kanallar
http://127.0.0.1:8000/messages/ – Xabarlar
http://127.0.0.1:8000/phones/ – Telefonlar
http://127.0.0.1:8000/admin/ – Django admin
5. 🔍 Qidiruv Funksiyalari
5.1. Kanallar sahifasi (/channels/)
Qidirish: Kanal nomi bo'yicha
Misol: "Yuk", "Transport", "Logistika"
5.2. Xabarlar sahifasi (/messages/)
Qidirish: Xabar matni, yo'nalish
Filtrlar:
Kanal bo'yicha
Sana oralig'i (dan / gacha)
Misol: "Toshkent", "Samarqand", "meva"
5.3. Statistika sahifasi (/stats/<channel_id>/)
Qidirish:
Yo'nalishlar (Qayerdan/Qayerga)
Yuk turlari
Transport turlari
Filtrlar: Sana oralig'i
Excel eksport: Statistikani yuklash
5.4. Telefonlar sahifasi (/phones/)
Qidirish: Telefon raqam
Misol: "+998", "90", "123"
5.5. Telefon xabarlari (/phones/messages/<phone>/)
Qidirish: Konkret telefon uchun xabar matni
Ko'rinish: Card layout (yorqin dizayn)
6. Telegram Login Oqimi
Telefon raqam - +998... formatida kiriting
SMS kodi - Telegram'dan kelgan kodni yozing
2-bosqichli parol - Agar yoqilgan bo'lsa (ixtiyoriy)
Sessiya saqlash - Keyingi kirishlarda avtomatik login
7. Paginatsiya
Barcha sahifalarda 20 tadan yozuv ko'rsatiladi
⬅ Oldingi / Keyingi ➡ tugmalari
Sahifa X / Y ko'rsatkichi
8. Excel Eksport
Statistika sahifasidan:

/stats/<channel_id>/export-excel/
Tarkibi:

Yo'nalishlar (A → B)
Yuk turlari
Transport turlari
To'lov turlari
9. JSON Eksport
/export-json/
Barcha xabarlarni JSON formatda saqlaydi.

10. Fayllar Strukturasi
logistic_tracker/
├── telegram_app/
│   ├── views.py          # Search funksiyalari bilan
│   ├── models.py         # Database modellari
│   ├── urls.py           # URL routing
│   ├── utils.py          # Yordamchi funksiyalar
│   └── templates/
│       └── telegram_app/
│           ├── channels.html          # Kanallar + search
│           ├── messages.html          # Xabarlar + filter
│           ├── channel_stats.html     # Statistika + search
│           ├── phones.html            # Telefonlar + search
│           └── phone_messages.html    # Telefon xabarlari
├── config/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── .env
11. Qidiruv Parametrlari (GET)
Kanallar:
?search=Yuk
Xabarlar:
?search=Toshkent&channel=123&date_from=2024-01-01&date_to=2024-12-31
Statistika:
?search=Samarqand&date_from=2024-01-01
Telefonlar:
?search=+998
12. Production Deploy
bash
# Debug o'chirish
DEBUG=False

# Static fayllar
python manage.py collectstatic

# Gunicorn bilan ishga tushirish
gunicorn config.wsgi:application --bind 0.0.0.0:8000
13. Xavfsizlik
⚠️ Shaxsiy Telegram akkauntingiz bilan ishlaydi
⚠️ Telegram ToS qoidalariga rioya qiling
⚠️ .env faylini GitHub'ga yuklamang
⚠️ Production'da SECRET_KEY ni o'zgartiring
14. Muammolarni Hal Qilish
Sessiya xatosi:
bash
python manage.py shell
from telegram_app.models import TelegramSession
TelegramSession.objects.all().delete()
Migration xatosi:
bash
python manage.py makemigrations
python manage.py migrate
15. Hissa Qo'shish
Pull request yuborishdan oldin:

Kodni formatlang (PEP8)
Test qiling
README'ni yangilang
16. Litsenziya
MIT License

17. Bog'lanish
GitHub: @Salohiddin08
Muammo haqida xabar: Issues
Loyiha muvaffaqiyatli ishlashi uchun omad tilaymiz! 🚀

