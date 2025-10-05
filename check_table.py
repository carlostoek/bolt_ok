import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('sqlite+aiosqlite:///bot.db')
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT sql FROM sqlite_master WHERE type="table" AND name="compatibility_quizzes"'))
        row = result.scalar()
        if row:
            print("Table exists:")
            print(row)
        else:
            print("Table does NOT exist")
    await engine.dispose()

asyncio.run(check())
