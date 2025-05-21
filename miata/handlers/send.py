from telegram import Bot


async def send_ad(bot: Bot, title, link, chat_id):
    text = f"{title}\n🔗 {link}"
    try:
        await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)
    except Exception as e:
        print(f"⚠️ Ошибка отправки объявления: {e}")
