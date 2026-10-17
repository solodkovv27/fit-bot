import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from aiogram import Router
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import datetime
import os
import asyncio

router = Router()

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def create_weight_chart(user_id: int, username: str):
    """Создаёт красивый график изменения веса"""
    
    async def get_data():
        return await db.get_weight_history(user_id, 30)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, get_data())
        history = future.result()
    
    if not history or len(history) < 2:
        return None
    
    weights = []
    dates = []
    
    for weight, date_str in history:
        weights.append(weight)
        try:
            date = datetime.datetime.fromisoformat(date_str)
        except:
            date = datetime.datetime.now()
        dates.append(date)
    
    dates.reverse()
    weights.reverse()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    
    ax.plot(dates, weights, color='#4CAF50', linewidth=3, marker='o', 
            markersize=8, markerfacecolor='white', markeredgewidth=2,
            markeredgecolor='#4CAF50', zorder=5)
    
    ax.fill_between(dates, weights, alpha=0.1, color='#4CAF50')
    
    ax.grid(True, alpha=0.3, linestyle='--', color='#cccccc')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
    
    plt.xticks(rotation=45, ha='right')
    
    ax.set_title(f'Progress: {username}', fontsize=16, fontweight='bold', 
                 pad=20, color='#2c3e50')
    
    ax.set_xlabel('Date', fontsize=12, color='#555555', labelpad=10)
    ax.set_ylabel('Weight (kg)', fontsize=12, color='#555555', labelpad=10)
    
    if len(weights) >= 2:
        diff = weights[0] - weights[-1]
        if diff > 0:
            status_text = f'Lost: {diff:.1f} kg'
            color = '#e74c3c'
        elif diff < 0:
            status_text = f'Gained: {abs(diff):.1f} kg'
            color = '#3498db'
        else:
            status_text = 'No change'
            color = '#95a5a6'
        
        ax.text(0.02, 0.98, status_text, transform=ax.transAxes,
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                color=color, fontweight='bold')
    
    ax.text(0.98, 0.98, f'Start: {weights[0]:.1f} kg\nCurrent: {weights[-1]:.1f} kg',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.tight_layout()
    
    filename = f'weight_chart_{user_id}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filename

@router.callback_query(lambda c: c.data == "go_charts")
async def go_charts(callback: CallbackQuery):
    await callback.answer()
    
    p = await db.get_user_profile(callback.from_user.id)
    if not p:
        await callback.message.answer("Сначала пройди регистрацию /start")
        return
    
    username = p[1]
    
    chart_file = create_weight_chart(callback.from_user.id, username)
    
    if chart_file:
        photo = FSInputFile(chart_file)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"📊 <b>Твой прогресс</b>\n\nОтличная работа! Продолжай в том же духе! 💪",
            parse_mode="HTML"
        )
        
        try:
            os.remove(chart_file)
        except:
            pass
    else:
        await callback.message.answer(
            "📊 <b>График пока недоступен</b>\n\n"
            "Нужно минимум 2 записи веса для построения графика.\n"
            "Используй /weight чтобы записать вес!",
            parse_mode="HTML"
        )

@router.message(Command("charts"))
async def cmd_charts(message: Message):
    p = await db.get_user_profile(message.from_user.id)
    if not p:
        await message.answer("Сначала пройди регистрацию /start")
        return
    
    username = p[1]
    chart_file = create_weight_chart(message.from_user.id, username)
    
    if chart_file:
        photo = FSInputFile(chart_file)
        await message.answer_photo(
            photo=photo,
            caption=f"📊 <b>Твой прогресс</b>\n\nОтличная работа! Продолжай в том же духе! 💪",
            parse_mode="HTML"
        )
        try:
            os.remove(chart_file)
        except:
            pass
    else:
        await message.answer(
            "📊 <b>График пока недоступен</b>\n\n"
            "Нужно минимум 2 записи веса для построения графика.\n"
            "Используй /weight чтобы записать вес!",
            parse_mode="HTML"
        )