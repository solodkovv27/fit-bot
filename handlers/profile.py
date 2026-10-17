from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime
import database as db

router = Router()

class RegStates(StatesGroup):
    name = State()
    age = State()
    weight = State()
    target = State()
    calories = State()

class FoodStates(StatesGroup):
    meal = State()
    fname = State()
    fcal = State()

class WeightStates(StatesGroup):
    weight = State()

WATER_GOAL = 2000

def make_progress_bar(percent, length=10):
    filled = int(length * percent / 100)
    empty = length - filled
    return "\U0001F7E2" * filled + "\u26AA" * empty

def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="\u25C0\uFE0F Назад в меню", callback_data="go_menu")
    return kb.as_markup()

# ===== /start =====
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if await db.user_exists(message.from_user.id):
        await show_menu(message)
        return
    await message.answer(
        "<b>Добро пожаловать в FitLife Bot!</b>\n\n"
        "Я помогу тебе достичь идеальной формы! \U0001F4AA\n"
        "Давай создадим твой профиль.\n\n"
        "\U0001F464 <b>Как тебя зовут?</b>",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.name)

@router.message(RegStates.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Приятно познакомиться, " + message.text + "! \U0001F60A\n\n"
        "<b>Сколько тебе лет?</b> (введи число)",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.age)

@router.message(RegStates.age)
async def reg_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("\u26A0\uFE0F Пожалуйста, введи возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer(
        "\u2696\uFE0F <b>Какой у тебя текущий вес?</b>\n(в кг, например: 75.5)",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.weight)

@router.message(RegStates.weight)
async def reg_weight(message: Message, state: FSMContext):
    clean = "".join(filter(lambda x: x.isdigit() or x in ['.', ','], message.text))
    try:
        w = float(clean.replace(',', '.'))
        if w <= 0 or w > 500: raise ValueError
    except:
        await message.answer("\u26A0\uFE0F Введи вес числом.")
        return
    await state.update_data(weight=w)
    await message.answer(
        "\U0001F3AF <b>Какой целевой вес ты хочешь достичь?</b>\n(в кг)",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.target)

@router.message(RegStates.target)
async def reg_target(message: Message, state: FSMContext):
    clean = "".join(filter(lambda x: x.isdigit() or x in ['.', ','], message.text))
    try:
        t = float(clean.replace(',', '.'))
        if t <= 0 or t > 500: raise ValueError
    except:
        await message.answer("\u26A0\uFE0F Введи вес числом.")
        return
    await state.update_data(target=t)
    await message.answer(
        "<b>Сколько калорий в день ты хочешь потреблять?</b>\n\n"
        "\U0001F4A1 Обычно:\n"
        "\u2022 Для похудения: 1500-1800 ккал\n"
        "\u2022 Для поддержания: 2000-2200 ккал\n"
        "\u2022 Для набора массы: 2500+ ккал",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.calories)

@router.message(RegStates.calories)
async def reg_cal(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("\u26A0\uFE0F Введи число.")
        return
    cal_goal = int(message.text)
    data = await state.get_data()
    
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044C",
        age=data['age'],
        weight=data['weight'],
        target=data['target'],
        calorie_goal=cal_goal
    )
    await state.clear()
    
    diff = data['weight'] - data['target']
    if diff > 0:
        mot = "\U0001F525 Нужно сбросить " + str(round(diff, 1)) + " кг. Я помогу тебе каждый день!"
    elif diff < 0:
        mot = "\U0001F4AA Нужно набрать " + str(round(abs(diff), 1)) + " кг. Вместе мы сможем!"
    else:
        mot = "\u2728 Ты уже в идеальной форме! Будем поддерживать результат!"
    
    text = (
        "\U0001F389 <b>Профиль создан!</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F464 <b>Имя:</b> " + data['name'] + "\n"
        "\U0001F382 <b>Возраст:</b> " + str(data['age']) + " лет\n"
        "\u2696\uFE0F <b>Текущий вес:</b> " + str(data['weight']) + " кг\n"
        "\U0001F3AF <b>Цель:</b> " + str(data['target']) + " кг\n"
        "\U0001F525 <b>Калории:</b> " + str(cal_goal) + " ккал/день\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        + mot + "\n\n"
        "<b>Начнём путь к идеалу!</b>"
    )
    await message.answer(text, parse_mode="HTML")
    await show_menu(message)

# ===== МЕНЮ =====
@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await show_menu(message)

async def show_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F4A7 Вода", callback_data="go_water")
    kb.button(text="\U0001F34E Еда", callback_data="go_food")
    kb.button(text="\u2696\uFE0F Вес", callback_data="go_weight")
    kb.button(text="\U0001F464 Профиль", callback_data="go_profile")
    kb.button(text="\U0001F4CA Отчёт", callback_data="go_report")
    kb.button(text="\U0001F4C8 Графики", callback_data="go_charts")
    kb.adjust(2)
    await message.answer(
        "\U0001F3E0 <b>Главное меню</b>\n\nВыбери раздел:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )

@router.callback_query(lambda c: c.data == "go_menu")
async def go_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await show_menu(callback.message)

# ===== КНОПКА: ВОДА =====
@router.callback_query(lambda c: c.data == "go_water")
async def go_water(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    current = await db.get_daily_water(callback.from_user.id)
    remain = max(0, WATER_GOAL - current)
    progress = min(100, int((current / WATER_GOAL) * 100))
    bar = make_progress_bar(progress)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F4A7 +250 мл", callback_data="w250")
    kb.button(text="\U0001F4A7\U0001F4A7 +500 мл", callback_data="w500")
    kb.button(text="\u25C0\uFE0F Назад", callback_data="go_menu")
    kb.adjust(2)
    
    text = (
        "\U0001F4A7 <b>Трекер воды</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F4CA Прогресс:\n" + bar + " " + str(progress) + "%\n\n"
        "\u2705 Выпито: <b>" + str(current) + " мл</b>\n"
        "\U0001F3AF Цель: <b>2000 мл</b>\n"
        "\u23F3 Осталось: <b>" + str(remain) + " мл</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@router.callback_query(lambda c: c.data in ["w250", "w500"])
async def add_water(callback: CallbackQuery):
    amount = 250 if callback.data == "w250" else 500
    await db.add_water(callback.from_user.id, amount)
    
    total = await db.get_daily_water(callback.from_user.id)
    remain = max(0, WATER_GOAL - total)
    progress = min(100, int((total / WATER_GOAL) * 100))
    bar = make_progress_bar(progress)
    
    text = (
        "\U0001F4A7 <b>Трекер воды</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\u2705 Добавлено: <b>+" + str(amount) + " мл</b>\n\n"
        "\U0001F4CA Прогресс:\n" + bar + " " + str(progress) + "%\n\n"
        "\U0001F4A6 Всего: <b>" + str(total) + " мл</b>\n"
        "\U0001F3AF Цель: <b>2000 мл</b>\n"
        "\u23F3 Осталось: <b>" + str(remain) + " мл</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
    )
    
    if total >= WATER_GOAL and (total - amount) < WATER_GOAL:
        text += "\n\n\U0001F389 <b>ПОЗДРАВЛЯЮ!</b>\nТы достиг дневной цели по воде!\nТы молодец! Так держать! \U0001F4A7"
    elif total >= WATER_GOAL:
        text += "\n\n\u2728 Отлично! Цель уже достигнута! Продолжай пить воду!"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F4A7 +250 мл", callback_data="w250")
    kb.button(text="\U0001F4A7\U0001F4A7 +500 мл", callback_data="w500")
    kb.button(text="\u25C0\uFE0F Назад", callback_data="go_menu")
    kb.adjust(2)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer("+" + str(amount) + " мл \u2705")

# ===== КНОПКА: ЕДА =====
@router.callback_query(lambda c: c.data == "go_food")
async def go_food(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    total = await db.get_daily_calories(callback.from_user.id)
    goal = await db.get_calorie_goal(callback.from_user.id)
    progress = min(100, int((total / goal) * 100)) if goal > 0 else 0
    bar = make_progress_bar(progress)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F305 Завтрак", callback_data="meal_breakfast")
    kb.button(text="\u2600\uFE0F Обед", callback_data="meal_lunch")
    kb.button(text="\U0001F319 Ужин", callback_data="meal_dinner")
    kb.button(text="\U0001F36A Перекус", callback_data="meal_snack")
    kb.button(text="\U0001F4CB История", callback_data="meal_history")
    kb.button(text="\u25C0\uFE0F Назад", callback_data="go_menu")
    kb.adjust(2)
    
    text = (
        "\U0001F34E <b>Трекер еды</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F4CA Прогресс:\n" + bar + " " + str(progress) + "%\n\n"
        "\U0001F525 Съедено: <b>" + str(total) + " ккал</b>\n"
        "\U0001F3AF Цель: <b>" + str(goal) + " ккал</b>\n"
        "\u23F3 Осталось: <b>" + str(max(0, goal - total)) + " ккал</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
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
                "\U0001F4CB <b>История пуста</b>\n\nСегодня ты ещё ничего не записал. Начни с завтрака! \U0001F305",
                parse_mode="HTML",
                reply_markup=back_button()
            )
        else:
            text = "\U0001F4CB <b>История за сегодня:</b>\n\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            for mt, fn, cal in history:
                em = {"breakfast":"\U0001F305","lunch":"\u2600\uFE0F","dinner":"\U0001F319","snack":"\U0001F36A"}.get(mt, "\U0001F37D\uFE0F")
                text += em + " <b>" + fn + "</b> \u2014 " + str(cal) + " ккал\n"
            total = await db.get_daily_calories(callback.from_user.id)
            text += "\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\U0001F525 <b>Итого: " + str(total) + " ккал</b>"
            await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button())
    else:
        names = {"breakfast":"завтрак \U0001F305","lunch":"обед \u2600\uFE0F","dinner":"ужин \U0001F319","snack":"перекус \U0001F36A"}
        await state.update_data(meal=action)
        await state.set_state(FoodStates.fname)
        await callback.message.answer(
            "\U0001F37D\uFE0F <b>Что ты съел на " + names[action] + "?</b>\n\nНапиши название продукта или блюда:",
            parse_mode="HTML"
        )

@router.message(FoodStates.fname)
async def food_name(message: Message, state: FSMContext):
    await state.update_data(fname=message.text)
    await message.answer(
        "\U0001F525 <b>Сколько калорий?</b>\n\n"
        "\U0001F4A1 Подсказка:\n"
        "\u2022 Яблоко: ~50 ккал\n"
        "\u2022 Куриная грудка (100г): ~165 ккал\n"
        "\u2022 Рис (100г): ~130 ккал\n"
        "\u2022 Хлеб (1 кусок): ~80 ккал\n\n"
        "Введи число:",
        parse_mode="HTML"
    )
    await state.set_state(FoodStates.fcal)

@router.message(FoodStates.fcal)
async def food_cal(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("\u26A0\uFE0F Введи число калорий.")
        return
    
    cal = int(message.text)
    data = await state.get_data()
    await db.add_food(message.from_user.id, data.get('meal','snack'), data.get('fname','Еда'), cal)
    await state.clear()
    
    total = await db.get_daily_calories(message.from_user.id)
    goal = await db.get_calorie_goal(message.from_user.id)
    
    em = {"breakfast":"\U0001F305","lunch":"\u2600\uFE0F","dinner":"\U0001F319","snack":"\U0001F36A"}.get(data.get('meal','snack'), "\U0001F37D\uFE0F")
    
    text = (
        "\u2705 <b>Записано!</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        + em + " <b>" + data.get('fname','Еда') + "</b>\n"
        "\U0001F525 Калории: <b>" + str(cal) + " ккал</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        "\U0001F4CA <b>Всего сегодня:</b>\n"
        "\U0001F525 " + str(total) + " / " + str(goal) + " ккал\n"
    )
    
    if total > goal:
        text += "\n\u26A0\uFE0F Ты превысил дневную норму на " + str(total - goal) + " ккал.\nНо не переживай, завтра новый день! \U0001F4AA"
    elif total >= goal * 0.9:
        text += "\n\U0001F525 Почти достиг цели! Осталось " + str(goal - total) + " ккал!"
    else:
        text += "\n\u2728 Отлично! Осталось " + str(goal - total) + " ккал до цели."
    
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())

# ===== КНОПКА: ВЕС =====
@router.callback_query(lambda c: c.data == "go_weight")
async def go_weight(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(WeightStates.weight)
    await callback.message.answer(
        "\u2696\uFE0F <b>Какой у тебя сейчас вес?</b>\n\nВведи вес в кг (например: 75.5)",
        parse_mode="HTML"
    )

@router.message(WeightStates.weight)
async def set_weight(message: Message, state: FSMContext):
    clean = "".join(filter(lambda x: x.isdigit() or x in ['.', ','], message.text))
    try:
        w = float(clean.replace(',', '.'))
        if w <= 0 or w > 500: raise ValueError
    except:
        await message.answer("\u26A0\uFE0F Введи вес числом.")
        return
    
    await db.update_user_weight(message.from_user.id, w)
    await state.clear()
    
    first, last = await db.get_weight_stats(message.from_user.id)
    if first and last:
        diff = first - last
        if diff > 0:
            prog = "\U0001F525 <b>Ты сбросил " + str(round(diff, 1)) + " кг!</b>\nОтличный прогресс! Так держать! \U0001F4AA"
        elif diff < 0:
            prog = "\U0001F4C8 Ты набрал " + str(round(abs(diff), 1)) + " кг.\nПродолжай работать!"
        else:
            prog = "\u2696\uFE0F Вес стабилен. Каждый день \u2014 это шаг вперёд!"
    else:
        prog = ""
    
    text = (
        "\u2705 <b>Вес обновлён!</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\u2696\uFE0F <b>Текущий вес: " + str(w) + " кг</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        + prog
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())

# ===== КНОПКА: ПРОФИЛЬ =====
@router.callback_query(lambda c: c.data == "go_profile")
async def go_profile(callback: CallbackQuery):
    await callback.answer()
    await show_profile(callback.message, callback.from_user.id)

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    await show_profile(message, message.from_user.id)

async def show_profile(message: Message, user_id: int):
    if not await db.user_exists(user_id):
        await message.answer("\u26A0\uFE0F Сначала пройди регистрацию командой /start", reply_markup=back_button())
        return
    
    p = await db.get_user_profile(user_id)
    if not p:
        await message.answer("\u26A0\uFE0F Ошибка получения профиля.", reply_markup=back_button())
        return
    
    uid = p[0]
    username = p[1]
    age = p[2]
    cw = p[3]
    tw = p[4]
    cg = p[5]
    
    cal = await db.get_daily_calories(user_id)
    water = await db.get_daily_water(user_id)
    
    cal_progress = min(100, int((cal / cg) * 100)) if cg > 0 else 0
    water_progress = min(100, int((water / WATER_GOAL) * 100))
    
    cal_bar = make_progress_bar(cal_progress)
    water_bar = make_progress_bar(water_progress)
    
    text = (
        "\U0001F464 <b>Твой профиль</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F464 <b>Имя:</b> " + str(username) + "\n"
        "\U0001F382 <b>Возраст:</b> " + str(age) + " лет\n"
        "\u2696\uFE0F <b>Вес:</b> " + str(cw) + " кг\n"
        "\U0001F3AF <b>Цель:</b> " + str(tw) + " кг\n"
        "\U0001F525 <b>Калории:</b> " + str(cg) + " ккал/день\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        "\U0001F4CA <b>Сегодня:</b>\n\n"
        "\U0001F525 Калории:\n" + cal_bar + " " + str(cal_progress) + "%\n"
        "   " + str(cal) + " / " + str(cg) + " ккал\n\n"
        "\U0001F4A7 Вода:\n" + water_bar + " " + str(water_progress) + "%\n"
        "   " + str(water) + " / 2000 мл\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())

# ===== КНОПКА: ОТЧЁТ =====
@router.callback_query(lambda c: c.data == "go_report")
async def go_report(callback: CallbackQuery):
    await callback.answer()
    await show_report(callback.message, callback.from_user.id)

@router.message(Command("report"))
async def cmd_report(message: Message):
    await show_report(message, message.from_user.id)

async def show_report(message: Message, user_id: int):
    if not await db.user_exists(user_id):
        await message.answer("\u26A0\uFE0F Сначала пройди регистрацию командой /start", reply_markup=back_button())
        return
    
    p = await db.get_user_profile(user_id)
    if not p:
        await message.answer("\u26A0\uFE0F Ошибка получения профиля.", reply_markup=back_button())
        return
    
    uid = p[0]
    username = p[1]
    age = p[2]
    cw = p[3]
    tw = p[4]
    cg = p[5]
    
    total_water, total_cal = await db.get_weekly_stats(user_id)
    avg_water = total_water // 7
    avg_cal = total_cal // 7
    
    first, last = await db.get_weight_stats(user_id)
    weight_diff = first - last if first and last else 0
    
    text = (
        "\U0001F4CA <b>Недельный отчёт</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F464 <b>" + str(username) + "</b>\n\n"
        "\U0001F4A7 <b>Вода за неделю:</b>\n"
        "   Всего: " + str(total_water) + " мл\n"
        "   В среднем: " + str(avg_water) + " мл/день\n"
        "   Цель: 2000 мл/день\n\n"
        "\U0001F525 <b>Калории за неделю:</b>\n"
        "   Всего: " + str(total_cal) + " ккал\n"
        "   В среднем: " + str(avg_cal) + " ккал/день\n"
        "   Цель: " + str(cg) + " ккал/день\n\n"
        "\u2696\uFE0F <b>Прогресс веса:</b>\n"
    )
    
    if weight_diff > 0:
        text += "   \U0001F525 Сброшено: " + str(round(weight_diff, 1)) + " кг\n"
    elif weight_diff < 0:
        text += "   \U0001F4C8 Набрано: " + str(round(abs(weight_diff), 1)) + " кг\n"
    else:
        text += "   \u2696\uFE0F Вес не изменился\n"
    
    if first:
        text += "   Начальный: " + str(first) + " кг\n"
    if last:
        text += "   Текущий: " + str(last) + " кг\n"
    
    text += "\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    
    if avg_water >= 1800:
        text += "\U0001F4A7 Отличный результат по воде! \U0001F31F\n"
    elif avg_water >= 1500:
        text += "\U0001F4A7 Хороший результат! Старайся пить больше!\n"
    else:
        text += "\U0001F4A7 Нужно пить больше воды! Цель: 2000 мл\n"
    
    if avg_cal <= cg:
        text += "\U0001F525 Ты вписываешься в норму калорий! \u2728"
    else:
        text += "\u26A0\uFE0F Превышение на " + str(avg_cal - cg) + " ккал/день. Попробуй снизить!"
    
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())

# ===== КОМАНДЫ =====
@router.message(Command("water"))
async def cmd_water(message: Message, state: FSMContext):
    await state.clear()
    current = await db.get_daily_water(message.from_user.id)
    remain = max(0, WATER_GOAL - current)
    progress = min(100, int((current / WATER_GOAL) * 100))
    bar = make_progress_bar(progress)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F4A7 +250 мл", callback_data="w250")
    kb.button(text="\U0001F4A7\U0001F4A7 +500 мл", callback_data="w500")
    kb.button(text="\u25C0\uFE0F Назад", callback_data="go_menu")
    kb.adjust(2)
    
    text = (
        "\U0001F4A7 <b>Трекер воды</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F4CA Прогресс:\n" + bar + " " + str(progress) + "%\n\n"
        "\u2705 Выпито: <b>" + str(current) + " мл</b>\n"
        "\U0001F3AF Цель: <b>2000 мл</b>\n"
        "\u23F3 Осталось: <b>" + str(remain) + " мл</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@router.message(Command("food"))
async def cmd_food(message: Message, state: FSMContext):
    await state.clear()
    total = await db.get_daily_calories(message.from_user.id)
    goal = await db.get_calorie_goal(message.from_user.id)
    progress = min(100, int((total / goal) * 100)) if goal > 0 else 0
    bar = make_progress_bar(progress)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="\U0001F305 Завтрак", callback_data="meal_breakfast")
    kb.button(text="\u2600\uFE0F Обед", callback_data="meal_lunch")
    kb.button(text="\U0001F319 Ужин", callback_data="meal_dinner")
    kb.button(text="\U0001F36A Перекус", callback_data="meal_snack")
    kb.button(text="\U0001F4CB История", callback_data="meal_history")
    kb.button(text="\u25C0\uFE0F Назад", callback_data="go_menu")
    kb.adjust(2)
    
    text = (
        "\U0001F34E <b>Трекер еды</b>\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "\U0001F4CA Прогресс:\n" + bar + " " + str(progress) + "%\n\n"
        "\U0001F525 Съедено: <b>" + str(total) + " ккал</b>\n"
        "\U0001F3AF Цель: <b>" + str(goal) + " ккал</b>\n"
        "\u23F3 Осталось: <b>" + str(max(0, goal - total)) + " ккал</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        "Выбери приём пищи:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@router.message(Command("weight"))
async def cmd_weight(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(WeightStates.weight)
    await message.answer(
        "\u2696\uFE0F <b>Какой у тебя сейчас вес?</b>\n\nВведи вес в кг (например: 75.5)",
        parse_mode="HTML"
    )
