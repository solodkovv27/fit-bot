import aiosqlite
import datetime

DB_NAME = "fitness_bot.db"
_db_pool = None

async def init_db():
    global _db_pool
    _db_pool = await aiosqlite.connect(DB_NAME)
    
    await _db_pool.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            age INTEGER,
            current_weight REAL,
            target_weight REAL,
            calorie_goal INTEGER DEFAULT 2000,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    await _db_pool.execute('''
        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weight REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    await _db_pool.execute('''
        CREATE TABLE IF NOT EXISTS water_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_ml INTEGER,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    await _db_pool.execute('''
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            meal_type TEXT,
            food_name TEXT,
            calories INTEGER,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    await _db_pool.commit()
    print("✅ Таблицы созданы/проверены")

async def user_exists(user_id: int) -> bool:
    async with _db_pool.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
        return row is not None

async def add_user(user_id: int, username: str, age: int, weight: float, target: float, calorie_goal: int = 2000):
    await _db_pool.execute(
        "INSERT INTO users (user_id, username, age, current_weight, target_weight, calorie_goal) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, age, weight, target, calorie_goal)
    )
    await _db_pool.execute("INSERT INTO weight_log (user_id, weight) VALUES (?, ?)", (user_id, weight))
    await _db_pool.commit()

async def get_user_profile(user_id: int):
    async with _db_pool.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
        return await cursor.fetchone()

async def update_user_weight(user_id: int, new_weight: float):
    await _db_pool.execute("UPDATE users SET current_weight = ? WHERE user_id = ?", (new_weight, user_id))
    await _db_pool.execute("INSERT INTO weight_log (user_id, weight) VALUES (?, ?)", (user_id, new_weight))
    await _db_pool.commit()

async def get_weight_stats(user_id: int):
    async with _db_pool.execute("SELECT weight FROM weight_log WHERE user_id = ? ORDER BY date ASC LIMIT 1", (user_id,)) as cursor:
        first_row = await cursor.fetchone()
    async with _db_pool.execute("SELECT weight FROM weight_log WHERE user_id = ? ORDER BY date DESC LIMIT 1", (user_id,)) as cursor:
        last_row = await cursor.fetchone()
    if first_row and last_row:
        return first_row[0], last_row[0]
    return None, None

async def add_water(user_id: int, amount: int):
    today = datetime.date.today().isoformat()
    await _db_pool.execute("INSERT INTO water_log (user_id, amount_ml, date) VALUES (?, ?, ?)", (user_id, amount, today))
    await _db_pool.commit()

async def get_daily_water(user_id: int):
    today = datetime.date.today().isoformat()
    async with _db_pool.execute("SELECT SUM(amount_ml) FROM water_log WHERE user_id = ? AND date = ?", (user_id, today)) as cursor:
        result = await cursor.fetchone()
        return result[0] if result[0] else 0

async def add_food(user_id: int, meal_type: str, name: str, calories: int):
    today = datetime.date.today().isoformat()
    await _db_pool.execute(
        "INSERT INTO food_log (user_id, meal_type, food_name, calories, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, meal_type, name, calories, today)
    )
    await _db_pool.commit()

async def get_daily_calories(user_id: int):
    today = datetime.date.today().isoformat()
    async with _db_pool.execute("SELECT SUM(calories) FROM food_log WHERE user_id = ? AND date = ?", (user_id, today)) as cursor:
        result = await cursor.fetchone()
        return result[0] if result[0] else 0

async def get_food_history(user_id: int):
    today = datetime.date.today().isoformat()
    async with _db_pool.execute(
        "SELECT meal_type, food_name, calories FROM food_log WHERE user_id = ? AND date = ? ORDER BY id",
        (user_id, today)
    ) as cursor:
        return await cursor.fetchall()

async def get_calorie_goal(user_id: int):
    async with _db_pool.execute("SELECT calorie_goal FROM users WHERE user_id = ?", (user_id,)) as cursor:
        result = await cursor.fetchone()
        return result[0] if result else 2000

async def get_weekly_stats(user_id: int):
    today = datetime.date.today()
    total_water = 0
    total_cal = 0
    
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        date_str = date.isoformat()
        
        async with _db_pool.execute(
            "SELECT SUM(amount_ml) FROM water_log WHERE user_id = ? AND date = ?",
            (user_id, date_str)
        ) as cursor:
            result = await cursor.fetchone()
            total_water += result[0] if result[0] else 0
        
        async with _db_pool.execute(
            "SELECT SUM(calories) FROM food_log WHERE user_id = ? AND date = ?",
            (user_id, date_str)
        ) as cursor:
            result = await cursor.fetchone()
            total_cal += result[0] if result[0] else 0
    
    return total_water, total_cal

async def get_all_users():
    async with _db_pool.execute("SELECT user_id FROM users") as cursor:
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_weight_history(user_id: int, days: int = 30):
    async with _db_pool.execute(
        "SELECT weight, date FROM weight_log WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, days)
    ) as cursor:
        return await cursor.fetchall()