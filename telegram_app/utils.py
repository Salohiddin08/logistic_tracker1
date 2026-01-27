import json
import re
from .models import TelegramMessage

def save_messages_json():
    """Barcha xabarlarni tahlil qilib JSON faylga saqlash."""
    qs = TelegramMessage.objects.all()
    all_extracted_shipments = []

    for m in qs:
        # Bitta xabardan bir nechta yuklarni sug'urib olamiz
        shipments = parse_shipment_text(m.text)
        
        for ship in shipments:
            data = {
                "channel_id": m.channel_id,
                "user_id": m.user_id,
                "date": m.date.isoformat(),
                "text_original": m.text,  # Asl matn (ixtiyoriy)
                **ship  # Parsing natijalari (origin, destination, va h.k.)
            }
            all_extracted_shipments.append(data)

    with open("telegram_messages.json", "w", encoding="utf-8") as f:
        json.dump(all_extracted_shipments, f, ensure_ascii=False, indent=4)
import re

def parse_shipment_text(text: str) -> list:
    """Xabarni telefon raqamlari zanjiri asosida bo'laklarga bo'ladi."""
    if not text:
        return []

    # 1. Xabarni bloklarga ajratish.
    # Regex har bir telefon raqami (+998...) dan keyin matnni bo'ladi.
    # Musbat qarash (lookbehind) orqali raqamlardan keyin bo'lishni amalga oshiramiz.
    blocks = re.split(r'(?<=\+\d{12})|(?<=\d{9})|(?=СРОЧНО)', text)
    
    results = []
    for block in blocks:
        block = block.strip()
        if len(block) < 15: # Juda qisqa qismlarni tashlaymiz
            continue
            
        parsed = _parse_single_block(block)
        
        # FILTR: Faqat yo'nalishi (A va B shahar) aniq bo'lgan yuklarni olamiz.
        # Bu "-" yoki bo'sh yuklar bazaga tushishini oldini oladi.
        if parsed["origin"] and (parsed["destination"] or parsed["phone"]):
            results.append(parsed)
            
    return results

def _parse_single_block(text: str) -> dict:
    """Bitta blok ichidan ma'lumotlarni qidirish."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    origin = None
    destination = None
    
    # Shahar nomlarini tozalash uchun regex (faqat harflar va bo'shliq)
    clean_regex = r'[^A-ZА-Яa-zа-я\s]'
    
    # 1. Yo'nalishni aniqlash
    # Namuna bo'yicha: birinchi 1-2 qator odatda origin va destination bo'ladi
    separators = ["—", "–", "→", "➝", "-", ":"]
    
    route_found = False
    for ln in lines:
        if any(sep in ln for sep in separators):
            for sep in separators:
                if sep in ln:
                    parts = ln.split(sep, 1)
                    origin = re.sub(clean_regex, '', parts[0]).strip()
                    destination = re.sub(clean_regex, '', parts[1]).strip()
                    route_found = True
                    break
        if route_found: break

    # Agar separator bo'lmasa, namunadagi kabi birinchi 2 ta qatorni olamiz
    if not route_found and len(lines) >= 2:
        origin = re.sub(clean_regex, '', lines[0]).strip()
        destination = re.sub(clean_regex, '', lines[1]).strip()
        # Shahar nomlari juda uzun bo'lsa (masalan butun boshli gap), bekor qilamiz
        if len(origin) > 30 or len(destination) > 30:
            origin, destination = None, None

    # 2. Qo'shimcha ma'lumotlar
    cargo_type = next((ln for ln in lines if any(x in ln.upper() for x in ["ГРУЗ", "ЮК", "YUK"])), None)
    truck_type = next((ln for ln in lines if any(x in ln.upper() for x in ["ТЕНТ", "РЕФ", "ФУРА", "120", "96"])), None)
    payment_type = next((ln for ln in lines if any(x in ln.upper() for x in ["НАХТ", "NAL", "ОПЛАТА", "ПЕРЕЧИС"])), None)
    
    # 3. Telefon raqami
    phones = re.findall(r"\+?\d[\d\s\-\(\)]{8,}\d", text)
    phone = phones[0].strip() if phones else None

    return {
        "origin": origin,
        "destination": destination,
        "cargo_type": cargo_type,
        "truck_type": truck_type,
        "payment_type": payment_type,
        "phone": phone,
    }