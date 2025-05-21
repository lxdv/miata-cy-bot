import os

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from miata.handlers.admin import forward_user_message, subscribers_command
from miata.handlers.etc import handle_callback, start_command
from miata.handlers.messages import available_command, randompost_command
from miata.handlers.subscriptions import (
    subscribe_command,
    unsubscribe_command,
)
from miata.redis_utils import RedisClient


class MiataBot:
    def __init__(self):
        if os.getenv("REDIS_PASSWORD") is None:
            raise ValueError("REDIS_PASSWORD environment variable is not set.")
        if os.getenv("TELEGRAM_BOT_TOKEN") is None:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")
        if os.getenv("ADMIN_CHAT_ID") is None:
            raise ValueError("ADMIN_CHAT_ID environment variable is not set.")

        self.redis_client = RedisClient(
            password=os.getenv("REDIS_PASSWORD"),
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
        )

        self.admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

        self.application = ApplicationBuilder().token(telegram_token).build()

        self.application.add_handler(
            CommandHandler("subscribers", subscribers_command(self.redis_client, self.admin_chat_id))
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message(self.admin_chat_id))
        )

        self.application.add_handler(
            CommandHandler("subscribe", subscribe_command(self.redis_client))
        )
        self.application.add_handler(
            CommandHandler("unsubscribe", unsubscribe_command(self.redis_client))
        )
        self.application.add_handler(CommandHandler("available", available_command))
        self.application.add_handler(CommandHandler("randompost", randompost_command(self.redis_client)))
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", start_command))

        self.application.add_handler(CallbackQueryHandler(handle_callback))

    async def initialize_commands(self):
        await self.application.bot.set_my_commands(
            [
                BotCommand("start", "Показать приветствие"),
                BotCommand("help", "Показать помощь"),
                BotCommand("available", "Показать текущие объявления"),
                BotCommand("subscribe", "Подписаться на обновления"),
                BotCommand("unsubscribe", "Отписаться от обновлений"),
                BotCommand("randompost", "Случайный пост из канала"),
            ]
        )

    async def run(self):
        await self.application.run_polling()
