from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import logging
import sys
import asyncio
from .handlers import router
from .keyboards import main_kb
import sqlite3
from .middlewares import AntiSpamMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Инициализация ---
import os
from dotenv import load_dotenv
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения!")

from aiogram.client.default import DefaultBotProperties
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.message.middleware(AntiSpamMiddleware(delay=1.0))
dp.callback_query.middleware(AntiSpamMiddleware(delay=1.0))
dp.include_router(router)

API_URL = os.getenv("API_BASE_URL", "http://api:8000")

def get_all_user_ids():
    conn = sqlite3.connect("data/users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur = conn.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return user_ids

async def notify_restart(bot):
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, "💢был рестарт", reply_markup=main_kb)
        except Exception as e:
            pass

async def on_startup(dispatcher):
    logger.info("Бот успешно запущен!")
    logger.info(f"Проверка подключения к API: {API_URL}")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "healthy":
                        logger.info("API сервис доступен!")
                    else:
                        logger.warning("API сервис отвечает, но не полностью здоров!")
                else:
                    logger.error(f"API сервис не отвечает: {resp.status}")
    except Exception as e:
        logger.error(f"Ошибка подключения к API: {e}")
    logger.info("Запуск polling...")
    await notify_restart(bot)

async def on_shutdown(dispatcher):
    logger.warning("Бот завершает работу (graceful shutdown)...")

async def main():
    try:
        await on_startup(dp)
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        await on_shutdown(dp)
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main()) 