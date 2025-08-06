import asyncio
import random

from telegram import Update
from telegram.ext import ContextTypes

from miata.handlers.send import send_ad
from miata.parser import get_from_bazaraki

def randompost_command(redis_client):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        posts = redis_client.get_posts()
        if not posts:
            await update.message.reply_text("📭 Пока нет сохранённых постов.")
            return
        post = random.choice(posts)
        await update.message.reply_text(post, disable_notification=True)

    return handler

def randomfact_command(gpt_model):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        fact = gpt_model.evaluate()
        await update.message.reply_text(fact, parse_mode="Markdown")

    return handler

async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Подожди немного, ищу объявления...")
    ads = get_from_bazaraki()
    if not ads:
        await update.message.reply_text("🚫 Объявления не найдены.")
        return
    for title, link in ads:
        await send_ad(context.bot, title, link, update.message.chat_id)
        await asyncio.sleep(1)
