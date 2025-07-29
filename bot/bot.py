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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

def get_bot_and_dispatcher():
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.message.middleware(AntiSpamMiddleware(delay=0.1))
    dp.callback_query.middleware(AntiSpamMiddleware(delay=0.1))
    dp.include_router(router)
    return bot, dp

bot, dp = get_bot_and_dispatcher()

# FastAPI приложение для webhook
app = FastAPI(
    title="Weather Bot Webhook Server",
    description="Webhook сервер для Telegram бота",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Webhook endpoints
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Weather Bot Webhook Server работает! 🤖"}

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "bot_token_configured": bool(os.getenv("BOT_TOKEN"))}

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Обработка webhook от Telegram"""
    try:
        update = await request.json()
        await dp.feed_webhook_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/webhook")
async def webhook_info():
    """Информация о webhook"""
    return {
        "webhook_status": "active",
        "endpoint": "/webhook",
        "description": "Telegram webhook endpoint"
    }

@app.on_event("startup")
async def fastapi_startup():
    """Инициализация FastAPI приложения"""
    logger.info("FastAPI webhook сервер запущен")
    
    # Настройка webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        try:
            await bot.set_webhook(
                url=f"{webhook_url}/webhook",
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook настроен: {webhook_url}/webhook")
        except Exception as e:
            logger.error(f"Ошибка настройки webhook: {e}")

@app.on_event("shutdown")
async def fastapi_shutdown():
    """Очистка при остановке FastAPI"""
    try:
        await bot.delete_webhook()
        logger.info("Webhook удален")
    except Exception as e:
        logger.error(f"Ошибка удаления webhook: {e}")
    logger.info("FastAPI webhook сервер остановлен")

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
    
    await notify_restart(bot)

async def on_shutdown(dispatcher):
    logger.warning("Бот завершает работу (graceful shutdown)...")

async def main_polling():
    try:
        await on_startup(dp)
        logger.info("Бот запущен в режиме polling!")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        await on_shutdown(dp)
        sys.exit(0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot.bot:app", host="0.0.0.0", port=8001, reload=False) 