from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from rich.console import Console
import sys
import asyncio
from .handlers import router
from .keyboards import main_kb
import sqlite3
from .middlewares import AntiSpamMiddleware

console = Console()

# --- Инициализация ---
import os
from dotenv import load_dotenv
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения!")
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.message.middleware(AntiSpamMiddleware(delay=1.0))
dp.callback_query.middleware(AntiSpamMiddleware(delay=1.0))
dp.include_router(router)

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_all_user_ids():
    conn = sqlite3.connect("users.db")
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
            print(f"Не удалось отправить сообщение {user_id}: {e}")

async def on_startup(dispatcher):
    console.print("[bold green]Бот успешно запущен![/bold green]")
    console.print(f"[bold purple]Проверка подключения к API: {API_URL}[/bold purple]")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "healthy":
                        console.print("[bold green]API сервис доступен![/bold green]")
                    else:
                        console.print("[bold yellow]API сервис отвечает, но не полностью здоров![/bold yellow]")
                else:
                    console.print(f"[bold red]API сервис не отвечает: {resp.status}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Ошибка подключения к API: {e}[/bold red]")
    console.print("[bold blue]Запуск polling...[/bold blue]")
    await notify_restart(bot)

async def on_shutdown(dispatcher):
    console.print("[bold yellow]Бот завершает работу (graceful shutdown)...[/bold yellow]")

async def main():
    try:
        await on_startup(dp)
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        await on_shutdown(dp)
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main()) 