from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

from .exports import build_shipments_workbook_bytes


@dataclass(frozen=True)
class BotConfig:
    token: str
    admin_chat_id: int


def get_bot_config() -> BotConfig:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN .env faylda yo'q")
    if not admin_chat_id:
        raise ValueError("TELEGRAM_ADMIN_CHAT_ID .env faylda yo'q")

    return BotConfig(token=token, admin_chat_id=int(admin_chat_id))


def _is_admin_chat(chat_id: int) -> bool:
    cfg = get_bot_config()
    return int(chat_id) == int(cfg.admin_chat_id)


async def _send_export(application: Application, *, days: int) -> None:
    from asgiref.sync import sync_to_async

    cfg = get_bot_config()

    if days < 1:
        days = 1
    if days > 60:
        days = 60

    today = timezone.localdate()
    date_from = today - timedelta(days=days - 1)
    date_to = today

    # ✅ TO'G'RILANDI: sync_to_async bilan chaqirish
    data = await sync_to_async(build_shipments_workbook_bytes)(days=days)
    filename = f"shipments_{date_from.isoformat()}_{date_to.isoformat()}.xlsx"

    await application.bot.send_document(
        chat_id=cfg.admin_chat_id,
        document=InputFile(data, filename=filename),
        caption=f"📊 *TG Yuk Monitor Hisobot*\n\n"
                f"📅 Sana: {date_from.isoformat()} → {date_to.isoformat()}\n"
                f"⏰ Muddat: {days} kun\n"
                f"✅ Fayl tayyor!",
        parse_mode='Markdown'
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i - chiroyli salomlashish"""
    if not update.effective_chat or not update.effective_user:
        return

    if not _is_admin_chat(update.effective_chat.id):
        await update.message.reply_text(
            "❌ *Kechirasiz!*\n\n"
            "Siz bu botdan foydalana olmaysiz.\n"
            "Faqat admin foydalanishi mumkin.",
            parse_mode='Markdown'
        )
        return

    # Foydalanuvchi ismini olish
    user = update.effective_user
    name = user.first_name or user.username or "Do'stim"

    # Chiroyli keyboard yaratish
    keyboard = [
        [
            InlineKeyboardButton("📊 Excel Export", callback_data="show_export_menu"),
        ],
        [
            InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
            InlineKeyboardButton("📈 Statistika", callback_data="stats"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 *Assalomu aleykum, {name}!*\n\n"
        f"🚛 *TG Yuk Monitor* botiga xush kelibsiz!\n\n"
        f"📦 Men sizga logistika ma'lumotlarini boshqarishda yordam beraman.\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha callback'larni boshqarish"""
    query = update.callback_query
    await query.answer()

    if not _is_admin_chat(query.message.chat_id):
        await query.edit_message_text("❌ Ruxsat yo'q!")
        return

    # Excel export menyusi
    if query.data == "show_export_menu":
        keyboard = [
            [
                InlineKeyboardButton("📅 1 kun", callback_data="export_1"),
                InlineKeyboardButton("📅 3 kun", callback_data="export_3"),
            ],
            [
                InlineKeyboardButton("📅 7 kun", callback_data="export_7"),
                InlineKeyboardButton("📅 14 kun", callback_data="export_14"),
            ],
            [
                InlineKeyboardButton("📅 30 kun", callback_data="export_30"),
                InlineKeyboardButton("📅 60 kun", callback_data="export_60"),
            ],
            [
                InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_main"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📊 *Excel Export*\n\n"
            "Ma'lumotlarni Excel formatida yuklash uchun muddatni tanlang:\n\n"
            "⏰ Kunlik avtomatik export: har kuni soat 00:05",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Yordam
    elif query.data == "help":
        keyboard = [
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "ℹ️ *Yordam*\n\n"
            "🤖 *Bot buyruqlari:*\n"
            "• /start - Botni ishga tushirish\n"
            "• /export [kunlar] - Excel yuklash\n\n"
            "📊 *Excel Export:*\n"
            "Telegram kanallaridagi yuk ma'lumotlarini\n"
            "Excel formatida yuklab olish.\n\n"
            "⏰ *Avtomatik export:*\n"
            "Har kuni soat 00:05 da avtomatik\n"
            "bugungi yuklar yuboriladi.\n\n"
            "🌐 *Web platforma:*\n"
            "To'liq statistika va boshqaruv uchun\n"
            "web platformadan foydalaning.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Statistika
    elif query.data == "stats":
        from asgiref.sync import sync_to_async
        from .models import Shipment

        today = timezone.localdate()

        # Bugungi yuklar
        today_count = await sync_to_async(
            lambda: Shipment.objects.filter(message__date__date=today).count()
        )()

        # Oxirgi 7 kun
        week_ago = today - timedelta(days=7)
        week_count = await sync_to_async(
            lambda: Shipment.objects.filter(message__date__date__gte=week_ago).count()
        )()

        # Oxirgi 30 kun
        month_ago = today - timedelta(days=30)
        month_count = await sync_to_async(
            lambda: Shipment.objects.filter(message__date__date__gte=month_ago).count()
        )()

        keyboard = [
            [InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📈 *Statistika*\n\n"
            f"📦 *Bugun:* {today_count} ta yuk\n"
            f"📅 *Oxirgi 7 kun:* {week_count} ta yuk\n"
            f"📊 *Oxirgi 30 kun:* {month_count} ta yuk\n\n"
            f"🕐 *Oxirgi yangilanish:* {timezone.now().strftime('%H:%M')}\n\n"
            f"💡 Batafsil ma'lumot uchun web platformadan foydalaning.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Orqaga qaytish
    elif query.data == "back_to_main":
        keyboard = [
            [
                InlineKeyboardButton("📊 Excel Export", callback_data="show_export_menu"),
            ],
            [
                InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
                InlineKeyboardButton("📈 Statistika", callback_data="stats"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        user = query.from_user
        name = user.first_name or user.username or "Do'stim"

        await query.edit_message_text(
            f"👋 *Xush kelibsiz, {name}!*\n\n"
            f"🚛 *TG Yuk Monitor*\n\n"
            f"Quyidagi tugmalardan birini tanlang:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Excel export
    elif query.data.startswith("export_"):
        days = int(query.data.split("_")[1])

        await query.edit_message_text(
            f"⏳ *Excel tayyorlanmoqda...*\n\n"
            f"📅 Muddat: {days} kun\n"
            f"⏱ Iltimos biroz kuting...",
            parse_mode='Markdown'
        )

        try:
            await _send_export(context.application, days=days)

            keyboard = [
                [InlineKeyboardButton("📊 Yana export", callback_data="show_export_menu")],
                [InlineKeyboardButton("◀️ Bosh sahifa", callback_data="back_to_main")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"✅ *Excel yuborildi!*\n\n"
                f"📊 Muddat: {days} kun\n"
                f"📥 Fayl yuqorida 👆",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            keyboard = [
                [InlineKeyboardButton("🔄 Qayta urinish", callback_data=query.data)],
                [InlineKeyboardButton("◀️ Orqaga", callback_data="show_export_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"❌ *Xatolik yuz berdi!*\n\n"
                f"Xato: {str(e)}\n\n"
                f"Iltimos qaytadan urinib ko'ring.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export buyrug'i - to'g'ridan-to'g'ri export"""
    if not update.effective_chat:
        return
    if not _is_admin_chat(update.effective_chat.id):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    days = 1
    if context.args:
        try:
            days = int(context.args[0])
        except Exception:
            days = 1

    await update.message.reply_text(
        f"⏳ *Excel tayyorlanmoqda...*\n\n"
        f"📅 Muddat: {days} kun\n"
        f"⏱ Iltimos kuting...",
        parse_mode='Markdown'
    )

    try:
        await _send_export(context.application, days=days)
        await update.message.reply_text(
            f"✅ *Yuborildi!*\n\n"
            f"📊 {days} kunlik ma'lumotlar Excel formatida yuborildi.",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Xatolik:* {str(e)}",
            parse_mode='Markdown'
        )


def build_application() -> Application:
    cfg = get_bot_config()

    application = ApplicationBuilder().token(cfg.token).build()

    # Handlerlar qo'shish
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('export', cmd_export))
    application.add_handler(CallbackQueryHandler(callback_handler))

    return application


async def daily_sender_loop(application: Application, *, hour: int = 0, minute: int = 5) -> None:
    """Har kuni avtomatik Excel yuborish"""
    while True:
        now = timezone.localtime()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)

        sleep_seconds = max(1, int((next_run - now).total_seconds()))
        await asyncio.sleep(sleep_seconds)

        try:
            await _send_export(application, days=1)
        except Exception:
            pass


async def send_export_now(*, days: int) -> None:
    """Web interfeysdan export (dashboard)"""
    application = build_application()
    await application.initialize()
    await application.bot.initialize()
    try:
        await _send_export(application, days=days)
    finally:
        await application.shutdown()