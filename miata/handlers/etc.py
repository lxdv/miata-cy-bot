from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

WELCOME_TEXT = (
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


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Эта кнопка пока не работает 🙂")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Кнопка! (не работает)", callback_data="noop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="Markdown", reply_markup=reply_markup
    )
