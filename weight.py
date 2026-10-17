from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db

router = Router()

class WeightStates(StatesGroup):
    weight = State()

def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад в меню", callback_data="go_menu")
    return kb.as_markup()

@router.callback_query(lambda c: c.data == "go_weight")
async def go_weight(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(WeightStates.weight)
    await callback.message.answer(
        "️ <b>Какой у тебя сейчас вес?</b>\n\nВведи вес в кг (например: 75.5)",
        parse_mode="HTML"
    )

@router.message(WeightStates.weight)
async def set_weight(message: Message, state: FSMContext):
    clean = "".join(filter(lambda x: x.isdigit() or x in ['.', ','], message.text))
    try:
        w = float(clean.replace(',', '.'))
        if w <= 0 or w > 500: raise ValueError
    except:
        await message.answer("⚠️ Введи вес числом.")
        return
    
    await db.update_user_weight(message.from_user.id, w)
    await state.clear()
    
    first, last = await db.get_weight_stats(message.from_user.id)
    if first and last:
        diff = first - last
        if diff > 0:
            prog = "🔥 <b>Ты сбросил " + str(round(diff, 1)) + " кг!</b>\nОтличный прогресс! 💪"
        elif diff < 0:
            prog = "📈 Ты набрал " + str(round(abs(diff), 1)) + " кг."
        else:
            prog = "⚖️ Вес стабилен."
    else:
        prog = ""
    
    text = (
        "✅ <b>Вес обновлён!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚖️ <b>Текущий вес: " + str(w) + " кг</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        + prog
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())

@router.message(lambda m: m.text and m.text.startswith("/weight"))
async def cmd_weight(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(WeightStates.weight)
    await message.answer(
        "️ <b>Какой у тебя сейчас вес?</b>\n\nВведи вес в кг (например: 75.5)",
        parse_mode="HTML"
    )
