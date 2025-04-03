import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime
import asyncio
import random
import os

# === ТВОИ ДАННЫЕ ===
TELEGRAM_BOT_TOKEN = os.getenv("7895859092:AAESvsmGrRhUJ7BSYcSYlm1idR7S3g4foQI")
ADMIN_CHAT_ID = os.getenv("589941059")  # Твой Telegram ID
SUBSCRIBERS_FILE = "subscribers.txt"
POSTS_FILE = "posts.txt"

# === URL с Mazda MX-5 ===
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

# === Хранилище ссылок и подписчиков
last_seen_url = None
subscribers = set()

# === Загрузка подписчиков из файла
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# === Сохранение подписчиков в файл
def save_subscribers():
    with open(SUBSCRIBERS_FILE, "w") as f:
        for chat_id in subscribers:
            f.write(f"{chat_id}\n")

subscribers = load_subscribers()

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

# === Команда /available
async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Подожди немного, ищу объявления...")
    ads = get_all_ads()
    if not ads:
        await update.message.reply_text("🚫 Объявления не найдены.")
        return
    for title, link in ads:
        await send_ad(context.bot, title, link, update.message.chat_id)
        await asyncio.sleep(1)

# === Команда /subscribe
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    subscribers.add(chat_id)
    save_subscribers()
    await update.message.reply_text("✅ Вы подписались на уведомления о новых объявлениях.")

# === Команда /unsubscribe
async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers()
        await update.message.reply_text("❎ Вы отписались от уведомлений.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# === Команда /randompost
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

# === Команда /start и /help
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
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
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# === Расписание 11:00 и 18:00
async def schedule_checks(bot: Bot):
    while True:
        now = datetime.datetime.now()
        if now.hour == 11 or now.hour == 18:
            print(f"🕓 {now.strftime('%H:%M')} — запуск проверки новых объявлений")
            await check_for_new_ad(bot)
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(300)

# === Запуск бота
async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("available", available_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("randompost", randompost_command))

    asyncio.create_task(schedule_checks(application.bot))

    print("🚗 Бот запущен. Ожидаю команды.")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
