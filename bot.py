import asyncio
import os
from aiogram import Bot, Dispatcher, F
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
from handlers.user_private import user_private_router
from handlers.admin_private import admin_private_router
from database.engine import create_db, session_marker
from middlewares.db import DataBaseSession


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot=bot)

dp.include_router(user_private_router)
dp.include_router(admin_private_router)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await create_db()
    dp.update.middleware(DataBaseSession(session_pool=session_marker))
    await dp.start_polling(bot, allowed_updates=['message'])

if __name__ == '__main__':
    try:
      asyncio.run(main())
    except:
      print("Бот лег")