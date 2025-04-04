import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import datetime
import asyncio
import random
import os
import nest_asyncio
nest_asyncio.apply()
from telegram.ext import CallbackQueryHandler


# === Константы ===
SUBSCRIBERS_FILE = "subscribers.txt"
POSTS_FILE = "posts.txt"
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

last_seen_url = None
subscribers = set()

# === Работа с подписчиками ===
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

# === Команды Telegram ===
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Показать приветствие и команды"),
        BotCommand("help", "Показать помощь"),
        BotCommand("available", "Показать все текущие объявления"),
        BotCommand("subscribe", "Подписаться на новые объявления"),
        BotCommand("unsubscribe", "Отписаться от уведомлений"),
        BotCommand("randompost", "Случайный пост из Miata CY"),
        BotCommand("subscribers", "Список подписчиков (только админ)"),
    ]
    await application.bot.set_my_commands(commands)

# === Сбор объявлений
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

# === Отправка одного объявления
async def send_ad(bot: Bot, title, link, chat_id):
    text = f"{title}\n🔗 {link}"
    try:
        await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка отправки объявления: {e}")

# === Проверка на новые объявления
async def check_for_new_ad(bot: Bot):
    global last_seen_url
    ads = get_all_ads()
    if ads:
        title, link = ads[0]
        if link != last_seen_url:
            last_seen_url = link
            print(f"🆕 Новое объявление: {title}")
            for user in subscribers:
                await send_ad(bot, title, link, user)
        else:
            print("⏳ Новых объявлений нет.")
    else:
        print("⚠️ Объявлений не найдено.")

# === Расписание — проверка каждый час
async def schedule_checks(bot: Bot):
    while True:
        now = datetime.datetime.now()
        print(f"⏰ Проверка объявлений ({now.strftime('%H:%M')})")
        await check_for_new_ad(bot)
        await asyncio.sleep(3600)

# === Команды ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Показать объявления", callback_data='available')],
        [InlineKeyboardButton("✅ Подписаться", callback_data='subscribe'),
         InlineKeyboardButton("❎ Отписаться", callback_data='unsubscribe')],
        [InlineKeyboardButton("🎲 Случайный пост", callback_data='randompost')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👋 Привет! Я бот, который следит за новыми объявлениями Mazda MX-5 на Bazaraki.\n\n"
        "📌 Доступные команды:\n"
        "  /available — покажу все текущие объявления\n"
        "  /subscribe — включить автоматические уведомления\n"
        "  /unsubscribe — отключить уведомления\n"
        "  /randompost — случайный пост из Miata CY 🚗\n"
        "  /start или /help — покажу это сообщение ещё раз\n\n"
        "🔕 Уведомления приходят *без звука*, чтобы не отвлекать 😊\n\n"
        "🛡️ *Дисклеймер:* Бот хранит только ваш Telegram ID, чтобы отправлять вам объявления.\n"
        "✉️ Вопросы? Просто напиши сообщение сюда!"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

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
    await update.message.reply_text("✅ Вы подписались на уведомления о новых объявлениях.")

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
            await update.message.reply_text("📭 Пока нет сохранённых постов.")
            return
        post = random.choice(posts)
        await update.message.reply_text(post, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка randompost: {e}")
        await update.message.reply_text("⚠️ Не удалось получить случайный пост.")

async def subscribers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("⛔ Эта команда только для администратора.")
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
        forwarded_text = f"📩 Сообщение от @{user.username or 'без ника'} (ID: {user.id}):\n{text}"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=forwarded_text)

# === Inline-кнопки
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'available':
        await available_command(update, context)
    elif query.data == 'subscribe':
        await subscribe_command(update, context)
    elif query.data == 'unsubscribe':
        await unsubscribe_command(update, context)
    elif query.data == 'randompost':
        await randompost_command(update, context)

# === Запуск бота
async def main():
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Команды
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", start_command))
        application.add_handler(CommandHandler("available", available_command))
        application.add_handler(CommandHandler("subscribe", subscribe_command))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        application.add_handler(CommandHandler("randompost", randompost_command))
        application.add_handler(CommandHandler("subscribers", subscribers_command))

        # Кнопки
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message))
        application.add_handler(CallbackQueryHandler(handle_callback))

        # Установим команды
        await set_bot_commands(application)

        # Расписание
        asyncio.create_task(schedule_checks(application.bot))

        print("🚗 Бот запущен. Ожидаю команды.")
        await application.run_polling()
    except Exception as e:
        print("⚠️ Ошибка при запуске:", e)

if __name__ == '__main__':
    asyncio.run(main())
