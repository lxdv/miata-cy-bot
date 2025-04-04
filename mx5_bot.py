import requests
from bs4 import BeautifulSoup
from telegram import (
    Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import datetime
import asyncio
import random
import os
import nest_asyncio

nest_asyncio.apply()

# === ТВОИ ДАННЫЕ ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# === Файлы ===
SUBSCRIBERS_FILE = "subscribers.txt"
POSTS_FILE = "posts.txt"
LAST_SEEN_FILE = "last_seen.txt"

# === URL с Mazda MX-5 ===
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

# === Подписчики ===
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

# === Последний пост ===
def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_seen(url):
    with open(LAST_SEEN_FILE, "w") as f:
        f.write(url)

last_seen_url = load_last_seen()

# === Парсинг объявлений ===
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

# === Отправка объявления ===
async def send_ad(bot: Bot, title, link, chat_id):
    text = f"{title}\n🔗 {link}"
    try:
        await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка отправки объявления: {e}")

# === Проверка нового объявления ===
async def check_for_new_ad(bot: Bot):
    global last_seen_url
    ads = get_all_ads()
    if ads:
        title, link = ads[0]
        if link != last_seen_url:
            last_seen_url = link
            save_last_seen(link)
            print(f"🆕 Новое объявление: {title}")
            for user in subscribers:
                await send_ad(bot, title, link, user)
        else:
            print("⏳ Новых объявлений нет.")
    else:
        print("⚠️ Объявлений не найдено.")

# === Команды ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Посмотреть объявления", callback_data="available")],
        [InlineKeyboardButton("✅ Подписаться", callback_data="subscribe"),
         InlineKeyboardButton("❎ Отписаться", callback_data="unsubscribe")],
        [InlineKeyboardButton("🎲 Случайный пост", callback_data="randompost")]
    ])
    text = (
        "👋 Привет! Я бот, который следит за новыми объявлениями Mazda MX-5 на Bazaraki.\n\n"
        "📌 Доступные команды:\n"
        "  /available — текущие объявления\n"
        "  /subscribe — подписаться на обновления\n"
        "  /unsubscribe — отписаться\n"
        "  /randompost — случайный пост Miata CY\n"
        "  /help — список команд\n\n"
        "✉️ Просто напиши сообщение — оно придёт админу!"
    )
    await update.message.reply_text(text, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)

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
    await update.message.reply_text("✅ Вы подписались на уведомления.")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers()
        await update.message.reply_text("❎ Вы отписались от уведомлений.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def randompost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(POSTS_FILE, "r") as f:
            posts = [line.strip() for line in f if line.strip()]
        if not posts:
            await update.message.reply_text("📭 Пока нет постов.")
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
        await update.message.reply_text("📭 Подписок нет.")
    else:
        await update.message.reply_text("📋 Подписчики:\n" + "\n".join(subscribers))

async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user = update.message.from_user
        text = update.message.text
        msg = f"📩 @{user.username or 'без ника'} (ID: {user.id}):\n{text}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)

# === Кнопки ===
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "available":
        ads = get_all_ads()
        if not ads:
            await query.message.reply_text("🚫 Объявления не найдены.")
            return
        for title, link in ads:
            await send_ad(context.bot, title, link, query.message.chat_id)
            await asyncio.sleep(1)

    elif query.data == "subscribe":
        chat_id = str(query.message.chat_id)
        subscribers.add(chat_id)
        save_subscribers()
        await query.message.reply_text("✅ Вы подписались.")

    elif query.data == "unsubscribe":
        chat_id = str(query.message.chat_id)
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            save_subscribers()
            await query.message.reply_text("❎ Вы отписались.")
        else:
            await query.message.reply_text("Вы не были подписаны.")

    elif query.data == "randompost":
        try:
            with open(POSTS_FILE, "r") as f:
                posts = [line.strip() for line in f if line.strip()]
            if not posts:
                await query.message.reply_text("📭 Постов нет.")
                return
            post = random.choice(posts)
            await query.message.reply_text(post, disable_notification=True)
        except Exception as e:
            print(f"⚠️ Ошибка кнопки randompost: {e}")
            await query.message.reply_text("⚠️ Ошибка при получении поста.")

# === Команды Telegram
async def set_bot_commands(app):
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("help", "Список команд"),
        BotCommand("available", "Текущие объявления"),
        BotCommand("subscribe", "Подписаться"),
        BotCommand("unsubscribe", "Отписаться"),
        BotCommand("randompost", "Случайный пост"),
    ]
    await app.bot.set_my_commands(commands)

# === Регулярная проверка
async def schedule_checks(bot: Bot):
    while True:
        await check_for_new_ad(bot)
        await asyncio.sleep(3600)

# === main
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("available", available_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    app.add_handler(CommandHandler("randompost", randompost_command))
    app.add_handler(CommandHandler("subscribers", subscribers_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await set_bot_commands(app)
    asyncio.create_task(schedule_checks(app.bot))

    print("🚗 Бот запущен.")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
