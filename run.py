import asyncio

import nest_asyncio

from miata.bot import MiataBot
from miata.handlers.subscriptions import schedule_sends

nest_asyncio.apply()


async def main():
    bot = MiataBot()
    
    asyncio.create_task(schedule_sends(bot.application.bot, bot.redis_client))

    await bot.initialize_commands()
    await bot.application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
