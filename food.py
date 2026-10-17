from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db

router = Router()

class FoodStates(StatesGroup):
    fname = State()
    fcal = State()

def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад в меню", callback_data="go_menu")
    return kb.as_markup()

@router.callback_query(lambda c: c.data == "go_food")
async def go_food(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    total = await db.get_daily_calories(callback.from_user.id)
    goal = await db.get_calorie_goal(callback.from_user.id)
    progress = min(100, int((total / goal) * 100)) if goal > 0 else 0
    
    kb = InlineKeyboardBuilder()
    kb.button(text=" Завтрак", callback_data="meal_breakfast")
    kb.button(text="☀️ Обед", callback_data="meal_lunch")
    kb.button(text="🌙 Ужин", callback_data="meal_dinner")
    kb.button(text=" Перекус", callback_data="meal_snack")
    kb.button(text="📋 История", callback_data="meal_history")
    kb.button(text="◀️ Назад", callback_data="go_menu")
    kb.adjust(2)
    
    text = (
        "🍎 <b>Трекер еды</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 Прогресс: " + str(progress) + "%\n\n"
        "🔥 Съедено: <b>" + str(total) + " ккал</b>\n"
        "🎯 Цель: <b>" + str(goal) + " ккал</b>\n"
        "⏳ Осталось: <b>" + str(max(0, goal - total)) + " ккал</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выбери приём пищи:"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@router.callback_query(lambda c: c.data.startswith("meal_"))
async def meal_click(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("meal_", "")
    await callback.answer()
    
    if action == "history":
        history = await db.get_food_history(callback.from_user.id)
        if not history:
            await callback.message.answer(
                "📋 <b>История пуста</b>\n\nСегодня ты ещё ничего не записал.",
                parse_mode="HTML",
                reply_markup=back_button()
            )
        else:
            text = "📋 <b>История за сегодня:</b>\n\n━━━━━━━━━━━━━━━━━━━━\n\n"
            for mt, fn, cal in history:
                em = {"breakfast":"🌅","lunch":"☀️","dinner":"🌙","snack":"🍪"}.get(mt, "🍽️")
                text += em + " <b>" + fn + "</b> — " + str(cal) + " ккал\n"
            total = await db.get_daily_calories(callback.from_user.id)
            text += "\n━━━━━━━━━━━━━━━━━━━━\n🔥 <b>Итого: " + str(total) + " ккал</b>"
            await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button())
    else:
        names = {"breakfast":"завтрак ","lunch":"обед ☀️","dinner":"ужин 🌙","snack":"перекус 🍪"}
        await state.update_data(meal=action)
        await state.set_state(FoodStates.fname)
        await callback.message.answer(
            "🍽️ <b>Что ты съел на " + names[action] + "?</b>\n\nНапиши название продукта:",
            parse_mode="HTML"
        )

@router.message(FoodStates.fname)
async def food_name(message: Message, state: FSMContext):
    await state.update_data(fname=message.text)
    await message.answer(
        "🔥 <b>Сколько калорий?</b>\n\nВведи число:",
        parse_mode="HTML"
    )
    await state.set_state(FoodStates.fcal)

@router.message(FoodStates.fcal)
async def food_cal(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("️ Введи число калорий.")
        return
    
    cal = int(message.text)
    data = await state.get_data()
    await db.add_food(message.from_user.id, data.get('meal','snack'), data.get('fname','Еда'), cal)
    await state.clear()
    
    total = await db.get_daily_calories(message.from_user.id)
    goal = await db.get_calorie_goal(message.from_user.id)
    
    text = (
        "✅ <b>Записано!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🍽️ <b>" + data.get('fname','Еда') + "</b>\n"
        "🔥 Калории: <b>" + str(cal) + " ккал</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 <b>Всего сегодня:</b>\n"
        "🔥 " + str(total) + " / " + str(goal) + " ккал\n"
    )
    
    if total > goal:
        text += "\n⚠️ Превышение на " + str(total - goal) + " ккал."
    else:
        text += "\n✨ Осталось " + str(goal - total) + " ккал до цели."
    
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())
