import os
import requests
import random
import datetime
import asyncio
from bs4 import BeautifulSoup
from telegram import (
    Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

import nest_asyncio
nest_asyncio.apply()

# === ТВОИ ДАННЫЕ ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # добавь этот секрет в Render
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # тоже как секрет в Render

# === Файлы
SUBSCRIBERS_FILE = "subscribers.txt"
POSTS_FILE = "posts.txt"
LAST_SEEN_FILE = "last_seen.txt"

# === URL с Mazda MX-5 ===
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

# === Хранилище подписчиков
subscribers = set()

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_subscribers():
    with open(SUBSCRIBERS_FILE, "w") as f:
        for chat_id in subscribers:
            f.write(f"{chat_id}\n")

subscribers = load_subscribers()

def get_last_seen_url():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_seen_url(url):
    with open(LAST_SEEN_FILE, "w") as f:
        f.write(url)

# === Получение всех объявлений
def get_all_ads():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    ads = soup.find_all("a", href=True, text=lambda t: t and "Mazda MX5" in t)

    results = []
    for tag in ads:
        title = tag.text.strip()
        link = "https://www.bazaraki.com" + tag['href']
        results.append((title, link))
    return results

# === Отправка объявления
async def send_ad(bot: Bot, title, link, chat_id):
    text = f"{title}\n🔗 {link}"
    try:
        await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка отправки объявления: {e}")

# === Проверка новых объявлений
async def check_for_new_ad(bot: Bot):
    ads = get_all_ads()
    if not ads:
        print("⚠️ Объявлений не найдено.")
        return

    title, link = ads[0]
    last_seen = get_last_seen_url()
    if link != last_seen:
        save_last_seen_url(link)
        print(f"🆕 Новое объявление: {title}")
        for user in subscribers:
            await send_ad(bot, title, link, user)
    else:
        print("⏳ Новых объявлений нет.")

# === Команды
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Показать объявления", callback_data="available")],
        [InlineKeyboardButton("🔔 Подписаться", callback_data="subscribe"),
         InlineKeyboardButton("🚫 Отписаться", callback_data="unsubscribe")],
        [InlineKeyboardButton("🎲 Случайный пост", callback_data="randompost")],
    ]
    welcome_text = (
        "👋 Привет! Я бот, который следит за новыми объявлениями Mazda MX-5 на Bazaraki.\n\n"
        "📌 Доступные команды:\n"
        "/available — все текущие объявления\n"
        "/subscribe — включить уведомления о новых объявлениях\n"
        "/unsubscribe — отключить уведомления\n"
        "/randompost — случайный пост из канала Miata CY 🚗\n"
        "/subscribers — список подписчиков (только для админа)\n"
        "/start или /help — это сообщение\n\n"
        "🔕 Уведомления приходят *без звука*, чтобы не отвлекать 😊\n\n"
        "🛡️ *Дисклеймер:* Бот хранит только ваш Telegram ID.\n"
        "✉️ Пиши прямо сюда, если будут вопросы!"
    )
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Подожди немного, ищу объявления...")
    ads = get_all_ads()
    if not ads:
        await update.message.reply_text("🚫 Объявления не найдены.")
        return
    for title, link in ads:
        await send_ad(context.bot, title, link, update.message.chat_id)
        await asyncio.sleep(1)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    subscribers.add(chat_id)
    save_subscribers()
    await update.message.reply_text("✅ Подписка активирована.")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers()
        await update.message.reply_text("❎ Подписка отключена.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def randompost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(POSTS_FILE, "r") as f:
            posts = [line.strip() for line in f if line.strip()]
        if not posts:
            await update.message.reply_text("📭 Пока нет сохранённых постов.")
            return
        post = random.choice(posts)
        await update.message.reply_text(post, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка randompost: {e}")
        await update.message.reply_text("⚠️ Не удалось получить пост.")

async def subscribers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("⛔ Только для администратора.")
        return
    if not subscribers:
        await update.message.reply_text("📭 Подписок пока нет.")
    else:
        text = "📋 Список подписчиков:\n" + "\n".join(subscribers)
        await update.message.reply_text(text)

async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user = update.message.from_user
        text = update.message.text
        forwarded = f"📩 Сообщение от @{user.username or 'без ника'} (ID: {user.id}):\n{text}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=forwarded)

# === Обработка inline кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    dummy_update = Update(update.update_id, message=query.message)
    dummy_update.message.chat_id = query.message.chat_id

    if data == "available":
        await available_command(dummy_update, context)
    elif data == "subscribe":
        await subscribe_command(dummy_update, context)
    elif data == "unsubscribe":
        await unsubscribe_command(dummy_update, context)
    elif data == "randompost":
        await randompost_command(dummy_update, context)

# === Установка списка команд для /
async def set_bot_commands(app):
    commands = [
        BotCommand("available", "Показать текущие объявления"),
        BotCommand("subscribe", "Подписаться на уведомления"),
        BotCommand("unsubscribe", "Отписаться от уведомлений"),
        BotCommand("randompost", "Случайный пост из Miata CY"),
        BotCommand("subscribers", "Список подписчиков (админ)"),
        BotCommand("help", "Справка и помощь"),
    ]
    await app.bot.set_my_commands(commands)

# === Запуск бота
async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("available", available_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("randompost", randompost_command))
    application.add_handler(CommandHandler("subscribers", subscribers_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    await set_bot_commands(application)
    asyncio.create_task(schedule_checks(application.bot))

    print("🚗 Бот запущен. Ожидаю команды.")
    await application.run_polling()

# === Планировщик
async def schedule_checks(bot: Bot):
    while True:
        await check_for_new_ad(bot)
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
