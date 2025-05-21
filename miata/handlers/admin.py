from telegram import Update
from telegram.ext import ContextTypes


def subscribers_command(redis_client, admin_chat_id):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        subscribers = redis_client.get_subscribers()

        if str(update.message.chat_id) != str(admin_chat_id):
            await update.message.reply_text("⛔ Эта команда только для администратора.")
            return
        if not subscribers:
            await update.message.reply_text("📭 Подписок пока нет.")
        else:
            text = "📋 Список подписчиков:\n" + "\n".join(subscribers)
            await update.message.reply_text(text)

    return handler


def forward_user_message(admin_chat_id):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.text:
            user = update.message.from_user
            text = update.message.text
            forwarded_text = f"📩 Сообщение от @{user.username or 'без ника'} (ID: {user.id}):\n{text}"
            await context.bot.send_message(chat_id=admin_chat_id, text=forwarded_text)

    return handler
