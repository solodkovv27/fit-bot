from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db

router = Router()
WATER_GOAL = 2000

@router.callback_query(lambda c: c.data.startswith("water_add_"))
async def add_water_callback(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    
    await db.add_water(callback.from_user.id, amount)
    new_total = await db.get_daily_water(callback.from_user.id)
    
    remaining = max(0, WATER_GOAL - new_total)
    
    text = (
        "💧 Трекер воды\n\n"
        "Добавлено: +" + str(amount) + " мл ✅\n"
        "Всего сегодня: " + str(new_total) + " мл\n"
        "Цель: " + str(WATER_GOAL) + " мл\n"
        "Осталось: " + str(remaining) + " мл"
    )
    
    if new_total >= WATER_GOAL and (new_total - amount) < WATER_GOAL:
        text += "\n\n🎉 ПОЗДРАВЛЯЮ! Ты достиг дневной цели по воде! Ты молодец! Так держать! 💪💧"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💧 +250 мл", callback_data="water_add_250")
    builder.button(text="💧💧 +500 мл", callback_data="water_add_500")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer("+" + str(amount) + " мл добавлено!")