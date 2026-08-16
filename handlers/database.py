import aiosqlite

DB_NAME = "bookings.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                service TEXT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        await db.commit()


async def add_booking(telegram_id, service, date, time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO bookings (telegram_id, service, date, time) VALUES (?, ?, ?, ?)",
            (telegram_id, service, date, time),
        )
        await db.commit()


async def get_user_bookings(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, service, date, time FROM bookings WHERE telegram_id = ? AND status = 'active'",
            (telegram_id,),
        )
        return await cursor.fetchall()


async def get_all_bookings():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT telegram_id, service, date, time FROM bookings WHERE status = 'active'"
        )
        return await cursor.fetchall()


async def cancel_booking(booking_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (booking_id,),
        )
        await db.commit()
