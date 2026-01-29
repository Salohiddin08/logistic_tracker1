import asyncio
import threading
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, PhoneNumberInvalidError

from .models import TelegramSession

logger = logging.getLogger(__name__)


def _run_async_in_thread(coro):
    """
    Helper function: async coroutine ni alohida threadda ishga tushirish
    """
    result = {'data': None, 'error': None}
    
    def run_in_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result['data'] = loop.run_until_complete(coro)
        except Exception as e:
            result['error'] = e
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()
    
    if result['error']:
        raise result['error']
    return result['data']


def _get_tg_credentials():
    """Telegram API credentials olish"""
    api_id = getattr(settings, 'TG_API_ID', None)
    api_hash = getattr(settings, 'TG_API_HASH', None)

    if not api_id or not api_hash:
        raise ValueError("TG_API_ID / TG_API_HASH .env faylda to'ldirilmagan")

    try:
        api_id = int(api_id)
    except Exception as exc:
        raise ValueError("TG_API_ID raqam (int) bo'lishi kerak") from exc

    return api_id, api_hash


# ==================== LOGIN VIEW ====================

def login_view(request):
    """
    Login sahifasi - username/password bilan kirish
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")
    
    return render(request, 'login.html')


# ==================== LOGOUT VIEW ====================

def logout_view(request):
    """Logout - tizimdan chiqish"""
    logout(request)
    messages.success(request, "Tizimdan chiqdingiz!")
    return redirect('login')


# ==================== TELEGRAM AUTH - PHONE ====================

async def _start_phone_login(phone: str):
    """Telegram telefon raqamiga kod yuborish"""
    api_id, api_hash = _get_tg_credentials()
    
    logger.info(f"📱 Telefon: {phone}")
    logger.info(f"🔑 API ID: {api_id}")
    
    client = TelegramClient(StringSession(), api_id, api_hash)
    
    try:
        await client.connect()
        logger.info("✅ Telegram serveriga ulandi")
        
        # ✅ Kod yuborish
        sent = await client.send_code_request(phone)
        logger.info(f"✅ Kod yuborildi! Phone code hash: {sent.phone_code_hash}")
        
        temp_session = client.session.save()
        
        return temp_session, sent.phone_code_hash
        
    except PhoneNumberInvalidError:
        logger.error("❌ Telefon raqam noto'g'ri!")
        raise ValueError("Telefon raqam noto'g'ri formatda! Masalan: +998901234567")
    except FloodWaitError as e:
        logger.error(f"❌ FloodWait: {e.seconds} soniya kuting")
        raise ValueError(f"Juda ko'p urinish! {e.seconds} soniya kutib, qaytadan urining.")
    except Exception as e:
        logger.error(f"❌ Xatolik: {str(e)}")
        raise
    finally:
        await client.disconnect()


def telegram_auth_phone(request):
    """
    Telegram auth - telefon raqam kiritish
    """
    if request.method == 'POST':
        phone = request.POST.get('phone_number', '').strip()
        
        if not phone:
            messages.error(request, "❌ Telefon raqamni kiriting!")
            return render(request, 'telegram_auth_phone.html')
        
        # ✅ Telefon raqamni formatlash
        # Bo'sh joy, tire, qavs va boshqalarni olib tashlash
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # + belgisini qo'shish (agar yo'q bo'lsa)
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Telefon raqam validatsiyasi
        if len(phone) < 10 or not phone[1:].isdigit():
            messages.error(request, "❌ Telefon raqam noto'g'ri! Masalan: +998901234567")
            return render(request, 'telegram_auth_phone.html')
        
        try:
            logger.info(f"🚀 Telegram kod yuborish boshlandi: {phone}")
            
            # Telegram'ga kod yuborish
            temp_session, phone_code_hash = _run_async_in_thread(_start_phone_login(phone))
            
            # Session'ga saqlash
            request.session['tg_phone'] = phone
            request.session['tg_temp_session'] = temp_session
            request.session['tg_phone_code_hash'] = phone_code_hash
            
            messages.success(request, f"✅ Kod yuborildi: {phone}")
            messages.info(request, "📱 Telegram'dan kelgan kodni kiriting")
            return redirect('telegram_auth_code')
            
        except ValueError as ve:
            messages.error(request, str(ve))
            return render(request, 'telegram_auth_phone.html')
        except Exception as exc:
            logger.error(f"❌ Exception: {exc}")
            messages.error(request, f"❌ Xatolik: {str(exc)}")
            messages.info(request, "💡 API ID va API HASH to'g'riligini tekshiring!")
            return render(request, 'telegram_auth_phone.html')
    
    return render(request, 'telegram_auth_phone.html')


# ==================== TELEGRAM AUTH - CODE ====================

async def _complete_phone_login(temp_session: str, phone: str, code: str, password: str | None, phone_code_hash: str | None):
    """Telegram kod bilan login tugallash"""
    api_id, api_hash = _get_tg_credentials()
    client = TelegramClient(StringSession(temp_session), api_id, api_hash)
    
    try:
        await client.connect()
        logger.info("✅ Client ulandi, kod tekshirilmoqda...")

        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if not password:
                raise ValueError("2FA parol kerak! Parolni kiriting.")
            await client.sign_in(password=password)

        # User ma'lumotlarini olish
        me = await client.get_me()
        user_id = me.id
        username = me.username or f"user_{user_id}"
        first_name = me.first_name or ""
        last_name = me.last_name or ""
        
        logger.info(f"✅ Login muvaffaqiyatli: {username}")
        
        return client.session.save(), user_id, username, first_name, last_name
    
    finally:
        await client.disconnect()


def telegram_auth_code(request):
    """
    Telegram auth - kod kiritish
    """
    phone = request.session.get('tg_phone')
    temp_session = request.session.get('tg_temp_session')
    phone_code_hash = request.session.get('tg_phone_code_hash')
    
    if not phone or not temp_session:
        messages.error(request, "❌ Sessiya tugagan. Qaytadan boshlang.")
        return redirect('telegram_auth_phone')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        password = request.POST.get('password', '').strip() or None
        
        if not code:
            messages.error(request, "❌ Kodni kiriting!")
            return render(request, 'telegram_auth_code.html', {'phone': phone})
        
        try:
            logger.info(f"🔐 Kod tekshirilmoqda: {code}")
            
            # Telegram login tugallash
            string_session, user_id, username, first_name, last_name = _run_async_in_thread(
                _complete_phone_login(temp_session, phone, code, password, phone_code_hash)
            )
            
            # ✅ Telegram Session saqlash (TUZATILGAN)
            api_id = getattr(settings, 'TG_API_ID', '')
            api_hash = getattr(settings, 'TG_API_HASH', '')
            
            # Avval barcha eski sessionlarni o'chirish
            deleted_count = TelegramSession.objects.all().delete()[0]
            logger.info(f"🗑️ {deleted_count} ta eski session o'chirildi")
            
            # Yangi session yaratish
            TelegramSession.objects.create(
                api_id=api_id,
                api_hash=api_hash,
                string_session=string_session,
            )
            logger.info("✅ Yangi Telegram session saqlandi")
            
            # Django User yaratish yoki topish
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            # Agar user yangi bo'lsa, parol o'rnatish sahifasiga yo'naltirish
            if created or not user.has_usable_password():
                request.session['user_id_for_password'] = user.id
                request.session.pop('tg_phone', None)
                request.session.pop('tg_temp_session', None)
                request.session.pop('tg_phone_code_hash', None)
                
                messages.success(request, "✅ Telegram orqali tasdiqlandi! Endi parol o'rnating.")
                return redirect('set_password')
            else:
                # User mavjud va parol bor - login qilish
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Session tozalash
                request.session.pop('tg_phone', None)
                request.session.pop('tg_temp_session', None)
                request.session.pop('tg_phone_code_hash', None)
                
                messages.success(request, f"✅ Xush kelibsiz, {user.first_name or user.username}!")
                return redirect('dashboard')
            
        except ValueError as ve:
            messages.error(request, str(ve))
            return render(request, 'telegram_auth_code.html', {'phone': phone})
        except Exception as exc:
            logger.error(f"❌ Kod xatosi: {exc}")
            messages.error(request, f"❌ Kod noto'g'ri yoki eskirgan: {str(exc)}")
            return render(request, 'telegram_auth_code.html', {'phone': phone})
    
    return render(request, 'telegram_auth_code.html', {'phone': phone})
    """
    Telegram auth - kod kiritish
    """
    phone = request.session.get('tg_phone')
    temp_session = request.session.get('tg_temp_session')
    phone_code_hash = request.session.get('tg_phone_code_hash')
    
    if not phone or not temp_session:
        messages.error(request, "❌ Sessiya tugagan. Qaytadan boshlang.")
        return redirect('telegram_auth_phone')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        password = request.POST.get('password', '').strip() or None
        
        if not code:
            messages.error(request, "❌ Kodni kiriting!")
            return render(request, 'telegram_auth_code.html', {'phone': phone})
        
        try:
            logger.info(f"🔐 Kod tekshirilmoqda: {code}")
            
            # Telegram login tugallash
            string_session, user_id, username, first_name, last_name = _run_async_in_thread(
                _complete_phone_login(temp_session, phone, code, password, phone_code_hash)
            )
            
            # Telegram Session saqlash
            api_id = getattr(settings, 'TG_API_ID', '')
            api_hash = getattr(settings, 'TG_API_HASH', '')
            
            TelegramSession.objects.update_or_create(
                api_id=api_id,
                defaults={
                    'api_hash': api_hash,
                    'string_session': string_session,
                }
            )
            
            # Django User yaratish yoki topish
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            # Agar user yangi bo'lsa, parol o'rnatish sahifasiga yo'naltirish
            if created or not user.has_usable_password():
                request.session['user_id_for_password'] = user.id
                request.session.pop('tg_phone', None)
                request.session.pop('tg_temp_session', None)
                request.session.pop('tg_phone_code_hash', None)
                
                messages.success(request, "✅ Telegram orqali tasdiqlandi! Endi parol o'rnating.")
                return redirect('set_password')
            else:
                # User mavjud va parol bor - login qilish
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Session tozalash
                request.session.pop('tg_phone', None)
                request.session.pop('tg_temp_session', None)
                request.session.pop('tg_phone_code_hash', None)
                
                messages.success(request, f"✅ Xush kelibsiz, {user.first_name or user.username}!")
                return redirect('dashboard')
            
        except ValueError as ve:
            messages.error(request, str(ve))
            return render(request, 'telegram_auth_code.html', {'phone': phone})
        except Exception as exc:
            logger.error(f"❌ Kod xatosi: {exc}")
            messages.error(request, f"❌ Kod noto'g'ri yoki eskirgan: {str(exc)}")
            return render(request, 'telegram_auth_code.html', {'phone': phone})
    
    return render(request, 'telegram_auth_code.html', {'phone': phone})


# ==================== SET PASSWORD ====================

def set_password_view(request):
    """
    Yangi username va parol o'rnatish
    """
    user_id = request.session.get('user_id_for_password')
    
    if not user_id:
        messages.error(request, "❌ Sessiya tugagan. Qaytadan login qiling.")
        return redirect('login')
    
    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not new_username or not password1 or not password2:
            messages.error(request, "❌ Barcha maydonlarni to'ldiring!")
            return render(request, 'set_password.html')
        
        if len(new_username) < 3:
            messages.error(request, "❌ Login kamida 3 ta belgidan iborat bo'lishi kerak!")
            return render(request, 'set_password.html')
        
        if not new_username.replace('_', '').isalnum():
            messages.error(request, "❌ Login faqat lotin harflari, raqamlar va _ belgisidan iborat bo'lishi kerak!")
            return render(request, 'set_password.html')
        
        if password1 != password2:
            messages.error(request, "❌ Parollar bir xil emas!")
            return render(request, 'set_password.html')
        
        if len(password1) < 6:
            messages.error(request, "❌ Parol kamida 6 ta belgidan iborat bo'lishi kerak!")
            return render(request, 'set_password.html')
        
        try:
            if User.objects.filter(username=new_username).exclude(id=user_id).exists():
                messages.error(request, f"❌ '{new_username}' login allaqachon band!")
                return render(request, 'set_password.html')
            
            user = User.objects.get(id=user_id)
            user.username = new_username
            user.set_password(password1)
            user.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('user_id_for_password', None)
            
            messages.success(request, f"✅ Xush kelibsiz, {user.first_name or user.username}!")
            return redirect('dashboard')
            
        except User.DoesNotExist:
            messages.error(request, "❌ User topilmadi!")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"❌ Xatolik: {str(e)}")
            return render(request, 'set_password.html')
    
    return render(request, 'set_password.html')


# ==================== FORGOT PASSWORD ====================

def forgot_password_view(request):
    """
    Parolni unutganlar uchun
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, "❌ Login nomini kiriting!")
            return render(request, 'forgot_password.html')
        
        try:
            user = User.objects.get(username=username)
            request.session['forgot_password_user_id'] = user.id
            
            messages.info(request, f"✅ Login topildi: {username}")
            return redirect('telegram_auth_phone')
            
        except User.DoesNotExist:
            messages.error(request, "❌ Bunday login topilmadi!")
            return render(request, 'forgot_password.html')
    
    return render(request, 'forgot_password.html')