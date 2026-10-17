import asyncio
import logging
import database as db

logger = logging.getLogger(__name__)

# Время напоминаний (часы, 24-часовой формат)
REMINDER_TIMES = {
    8: "Доброе утро! ☀️\n\nНе забудь выпить стакан воды и записать завтрак! 🌅\n\nИспользуй /food чтобы записать еду.",
    13: "Обеденное время! ️\n\nКак твой обед? Запиши калории, чтобы не потерять счёт!\n\nИспользуй /food → Обед",
    16: "Пора выпить воды! 💧\n\nТы уже выпил свою норму сегодня?\n\nИспользуй /water чтобы проверить.",
    19: "Ужин! 🌙\n\nНе забудь записать ужин и подвести итоги дня.\n\nИспользуй /food → Ужин",
    21: "Вечерний отчёт! 📊\n\nКак прошёл день?\n\nИспользуй /report чтобы посмотреть недельный отчёт.\nИспользуй /profile чтобы проверить прогресс."
}

async def send_reminders(bot):
    """Функция, которая отправляет напоминания каждый час"""
    logger.info("✅ Система напоминаний запущена")
    
    while True:
        try:
            # Получаем текущий час
            import datetime
            current_hour = datetime.datetime.now().hour
            current_minute = datetime.datetime.now().minute
            
            # Проверяем напоминания только в начале часа (0-я минута)
            if current_minute == 0 and current_hour in REMINDER_TIMES:
                message_text = REMINDER_TIMES[current_hour]
                
                # Получаем всех пользователей
                users = await db.get_all_users()
                
                if users:
                    logger.info(f"📤 Отправка напоминания в {current_hour}:00 для {len(users)} пользователей")
                    
                    for user_id in users:
                        try:
                            await bot.send_message(
                                user_id,
                                message_text,
                                parse_mode="HTML"
                            )
                            logger.info(f"✅ Напоминание отправлено пользователю {user_id}")
                        except Exception as e:
                            logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
                
                # Ждём 65 секунд, чтобы не отправить дважды
                await asyncio.sleep(65)
            else:
                # Проверяем каждые 30 секунд
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в системе напоминаний: {e}")
            await asyncio.sleep(60)