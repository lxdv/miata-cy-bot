import asyncio

from telegram import Bot, Update
from telegram.ext import ContextTypes

from miata.handlers.send import send_ad
from miata.parser import get_from_bazaraki


def subscribe_command(redis_client):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        subscribers = redis_client.get_subscribers()
        chat_id = str(update.message.chat_id)
        if chat_id in subscribers:
            await update.message.reply_text("⛔ Вы уже подписаны на уведомления.")
            return
        subscribers.add(chat_id)
        redis_client.set_subscribers(list(subscribers))
        await update.message.reply_text(
            "✅ Вы подписались на уведомления о новых объявлениях."
        )

    return handler


def unsubscribe_command(redis_client):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        subscribers = redis_client.get_subscribers()
        chat_id = str(update.message.chat_id)
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            redis_client.set_subscribers(list(subscribers))
            await update.message.reply_text("❎ Вы отписались от уведомлений.")
        else:
            await update.message.reply_text("⛔ Вы не были подписаны на уведомления.")

    return handler


def get_new_ads(redis_client, save_seen=True):
    seen = redis_client.get_seen()
    ads = get_from_bazaraki()
    new_ads = []
    for title, link in ads:
        if link not in seen:
            new_ads.append((title, link))
            seen.add(link)

    if save_seen:
        redis_client.set_seen(list(seen))

    return new_ads


async def send_new_ads(bot: Bot, redis_client):
    ads = get_new_ads(redis_client)
    subscribers = redis_client.get_subscribers()
    for title, link in ads:
        print(f"🆕 Новое объявление: {title} / {link}")
        for user in subscribers:
            await send_ad(bot, title, link, user)
            await asyncio.sleep(1)


async def schedule_sends(bot: Bot, redis_client):
    while True:
        print("🔄 Проверка объявлений по расписанию")
        await send_new_ads(bot, redis_client)
        await asyncio.sleep(3600)
