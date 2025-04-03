import time
import asyncio
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === ТВОИ ДАННЫЕ ===
TELEGRAM_BOT_TOKEN = '7895859092:AAESvsmGrRhUJ7BSYcSYlm1idR7S3g4foQI'
CHAT_ID = 589941059 # без кавычек

# === Ссылка на Mazda MX-5 ===
URL = "https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/mazda/mazda-mx5/"

# === Создание headless-браузера через Selenium ===
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# === Поиск всех ссылок с текстом Mazda MX5 ===
def get_all_ads():
    driver = create_driver()
    driver.get(URL)
    time.sleep(3)

    # Скроллим вниз, чтобы подгрузились все объявления
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    links = driver.find_elements(By.TAG_NAME, "a")
    results = []

    for link in links:
        try:
            text = link.text.strip()
            href = link.get_attribute("href")
            if "Mazda MX5" in text and href:
                print(f"✅ Найдено объявление: {text} — {href}")
                results.append((text, "—", href, None))  # без цены и фото
        except Exception as e:
            print("⚠️ Ошибка при парсинге ссылки:", e)

    driver.quit()
    print(f"🔍 Найдено Mazda-ссылок: {len(results)}")
    return results

# === Отправка объявления в Telegram ===
async def send_ad(update: Update, title, price, link, image_url):
    caption = f"{title}\nЦена: {price}\n🔗 {link}"
    try:
        await update.message.reply_text(caption)
    except Exception as e:
        print("⚠️ Ошибка при отправке:", e)

# === Проверка новых объявлений ===
last_seen_url = None
async def check_for_new(bot: Bot):
    global last_seen_url
    ads = get_all_ads()
    if ads:
        title, price, link, image_url = ads[0]
        if link != last_seen_url:
            last_seen_url = link
            print(f"🔔 Новое объявление: {title}")
            # нет update, поэтому отправка не возможна напрямую
        else:
            print("⏳ Новых объявлений нет.")
    else:
        print("⚠️ Объявления не найдены.")

# === Обработка команды /available ===
async def available_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 Команда /available получена")
    await update.message.reply_text("⏳ Подожди несколько секунд, я ищу свежие объявления...")
    ads = get_all_ads()
    if not ads:
        await update.message.reply_text("Нет доступных объявлений.")
        return
    for title, price, link, image_url in ads:
        await send_ad(update, title, price, link, image_url)
        await asyncio.sleep(1)

# === Обработка команды /start ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Привет! Я бот, который отслеживает новые объявления Mazda MX-5 на Bazaraki.\n\n"
        "📌 Я умею:\n"
        "• Проверять сайт дважды в день (в 11:00 и 18:00)\n"
        "• Присылать тебе новые объявления, как только они появятся\n"
        "• Показывать все доступные сейчас объявления по команде /available\n\n"
        "Напиши /available, чтобы посмотреть текущие предложения 💌"
    )
    await update.message.reply_text(welcome_text)

    # 🔔 Отправка уведомления владельцу
    user = update.effective_user
    alert_text = f"👀 Новый пользователь: {user.first_name} (@{user.username}) запустил бота!"
    try:
        await context.bot.send_message(chat_id=CHAT_ID, text=alert_text)
    except Exception as e:
        print("⚠️ Не удалось отправить уведомление владельцу:", e)

# === Проверка дважды в день ===
async def schedule_check(bot: Bot):
    while True:
        now = time.localtime()
        if now.tm_hour == 11 or now.tm_hour == 18:
            print(f"🕒 {now.tm_hour:02d}:{now.tm_min:02d} — проверка объявлений")
            await check_for_new(bot)
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(300)

# === Запуск бота ===
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("available", available_command))
    app.add_handler(CommandHandler("start", start_command))
    asyncio.create_task(schedule_check(app.bot))
    print("🚗 Бот запущен. Жду /available и проверяю в 11:00 и 18:00")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())