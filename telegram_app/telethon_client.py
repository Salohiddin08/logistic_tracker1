from telethon import TelegramClient
from telethon.sessions import StringSession


async def get_client(api_id: int, api_hash: str, string_session: str) -> TelegramClient:
    """Telethon clientni yaratish va start qilish.

    Har bir so'rov uchun alohida client yaratiladi, global clientlardan foydalanmaymiz.
    """
    client = TelegramClient(StringSession(string_session), api_id, api_hash)
    await client.start()
    return client


async def get_channels(client: TelegramClient):
    """Mavjud kanallar ro'yxatini qaytaradi."""
    channels = []
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            channels.append({
                "id": dialog.entity.id,
                "title": getattr(dialog.entity, "title", ""),
            })
    return channels


async def get_messages(client: TelegramClient, channel_id: int, limit: int = 100):
    """Kanal xabarlarini oladi.

    Telethon ko'pincha faqat oddiy `id` bo'yicha entity topa olmaydi va
    `ValueError: Could not find the input entity ...` xatosini beradi.
    Shu sababli bu funksiya avval `iter_dialogs()` orqali kerakli
    dialogni topib, to'g'ridan-to'g'ri entity obyektini ishlatadi.
    """
    target_entity = None
    async for dialog in client.iter_dialogs():
        if dialog.entity.id == channel_id:
            target_entity = dialog.entity
            break

    # Agar dialog topilmasa, bo'sh ro'yxat qaytaramiz (xato o'rniga)
    if target_entity is None:
        return []

    return await client.get_messages(target_entity, limit=limit)
