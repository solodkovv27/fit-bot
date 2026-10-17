import asyncio
import logging
from aiogram import Bot, Dispatcher

import config
import database as db
import profile
import water
import food
import weight
import reminders
import charts

logging.basicConfig(level=logging.INFO)

async def main():
    await db.init_db()
    print("✅ База данных инициализирована")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(profile.router)
    dp.include_router(water.router)
    dp.include_router(food.router)
    dp.include_router(weight.router)
    dp.include_router(charts.router)

    print("🚀 Бот запущен! Открой Telegram и напиши /start")
    
    asyncio.create_task(reminders.send_reminders(bot))
    print("⏰ Система напоминаний активирована")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
