import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import datetime
import asyncio
import random
import nest_asyncio

nest_asyncio.apply()

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = '7895859092:AAESvsmGrRhUJ7BSYcSYlm1idR7S3g4foQI'
OWNER_CHAT_ID = 589941059  # твой Telegram user ID
CHANNEL_USERNAME = 'miata_cy'

# === Переменные ===
subscribers = set()
last_seen_url = None

# === Сайт с Mazda MX-5 ===
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

def get_all_ads():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    ads = soup.find_all("a", href=True)
    results = []
    for tag in ads:
        text = tag.get_text(strip=True)
        href = tag["href"]
        if "mazda-mx5" in href.lower() and "Mazda MX5" in text:
            full_url = "https://www.bazaraki.com" + href
            results.append((text, full_url))
    return list(dict.fromkeys(results))  # удаляем дубликаты

# === Команды ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот, который следит за новыми объявлениями Mazda MX-5 на Bazaraki.\n\n"
        "📌 Доступные команды:\n"
        "  /available — покажу все текущие объявления (нужно подождать минутку)\n"
        "  /subscribe — включить автоматические уведомления о новых объявлениях\n"
        "  /unsubscribe — отключить уведомления\n"
        "  /randompost — случайный пост из канала Miata CY 🚗\n"
        "  /start или /help — покажу это сообщение ещё раз\n\n"
        "🔕 Уведомления приходят *без звука*, чтобы не отвлекать 😊\n\n"
        "🛡️ *Дисклеймер:* Бот хранит только ваш Telegram ID, чтобы отправлять вам объявления. Личные данные, сообщения или что-либо ещё — не собираются и не сохраняются.\n\n"
        "✉️ Если будут вопросы или предложения — пиши прямо сюда! 🙂"
    )

async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Подожди немного, ищу объявления...")
    ads = get_all_ads()
    if not ads:
        await update.message.reply_text("🙁 Объявлений не найдено.")
        return

    for title, link in ads:
        await update.message.reply_text(f"{title}\n{link}", disable_notification=True)
        await asyncio.sleep(1)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribers.add(user_id)
    await update.message.reply_text("✅ Уведомления включены! Я пришлю тебе новые объявления, как только они появятся.")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        await update.message.reply_text("❌ Уведомления отключены.")
    else:
        await update.message.reply_text("Ты не был в списке подписчиков.")

async def randompost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with context.bot.get_chat(CHANNEL_USERNAME) as channel:
            posts = await context.bot.get_chat_history(channel.id, limit=100)
            messages = [m for m in posts if m.text or m.caption]
            if messages:
                msg = random.choice(messages)
                if msg.photo:
                    await update.message.reply_photo(photo=msg.photo[-1].file_id, caption=msg.caption, disable_notification=True)
                else:
                    await update.message.reply_text(msg.text, disable_notification=True)
            else:
                await update.message.reply_text("Канал пока пуст.")
    except Exception as e:
        await update.message.reply_text("⚠️ Не удалось получить пост. Попробуй позже.")

async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    message = f"📩 Сообщение от @{user.username or user.first_name} (ID: {user.id}):\n{text}"
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=message)

# === Автоматическая проверка новых объявлений ===
async def check_for_new_ads(bot: Bot):
    global last_seen_url
    ads = get_all_ads()
    if ads:
        title, link = ads[0]
        if link != last_seen_url:
            last_seen_url = link
            text = f"🔔 Новое объявление!\n{title}\n{link}"
            for user_id in subscribers:
                try:
                    await bot.send_message(chat_id=user_id, text=text, disable_notification=True)
                except:
                    pass

async def scheduled_checker(bot: Bot):
    while True:
        now = datetime.datetime.now()
        if now.hour in [11, 18]:
            print("⏰ Запуск авто-проверки")
            await check_for_new_ads(bot)
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(300)

# === Основной запуск ===
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("available", available_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CommandHandler("randompost", randompost_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message))

    asyncio.create_task(scheduled_checker(app.bot))

    print("🚗 Бот запущен. Ожидаю команды.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
