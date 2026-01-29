# Logistic Tracker

**Logistic Tracker** — bu mahsulotlar va yuklarni kuzatish, jo‘natish va yetkazib berish jarayonlarini boshqarish uchun mo‘ljallangan web-ilova. Ushbu loyiha orqali kompaniyalar o‘z logistika operatsiyalarini avtomatlashtirib, real vaqt rejimida ma’lumotlarni kuzatishi mumkin.

---

## Asosiy xususiyatlar

* Mahsulot va jo‘natmalarni qo‘shish, tahrirlash va o‘chirish.
* Yetkazib berish jarayonini real vaqt rejimida kuzatish.
* Statistika va hisobotlar yaratish.
* Foydalanuvchilar uchun qulay va intuitiv interfeys.

---

## Texnologiyalar

* **Backend:** Python, Django/Flask (loyihaga mosini yoz)
* **Frontend:** HTML, CSS, JavaScript, React (agar ishlatilgan bo‘lsa)
* **Ma’lumotlar bazasi:** PostgreSQL/MySQL/SQLite
* **API:** REST API orqali ma’lumotlarni boshqarish

---

## O‘rnatish

1. Loyihani klonlash:

```bash
git clone https://github.com/username/logistic_tracker1.git
cd logistic_tracker
```

2. Virtual muhit yaratish va aktivlashtirish:

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. Zarur paketlarni o‘rnatish:

```bash
pip install -r requirements.txt
```

4. Ma’lumotlar bazasini sozlash va migratsiyalarni bajarish:

```bash
python manage.py migrate
```

5. Serverni ishga tushirish:

```bash
python manage.py runserver
```

6. Brauzer orqali tizimga kirish:

```
http://127.0.0.1:8000
```

---

## Foydalanish

* Foydalanuvchi hisobini yaratish.
* Mahsulotlar va jo‘natmalarni qo‘shish.
* Yetkazib berish jarayonini kuzatish va yangilash.
* Statistika va hisobotlarni ko‘rish.

---

## Hissa qo‘shish

Agar loyiha ochiq bo‘lsa, hissa qo‘shish uchun:

1. Fork qiling.
2. Yangi branch yarating: `git checkout -b feature-name`
3. O‘zgartirishlar kiritib commit qiling: `git commit -m "Add some feature"`
4. Branchni push qiling: `git push origin feature-name`
5. Pull request yuboring

