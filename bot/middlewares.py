from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.fsm.context import FSMContext
import time

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 1.0):
        super().__init__()
        self.delay = delay

    async def __call__(self, handler, event: Update, data: dict):
        state: FSMContext = data.get("state")
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, 'message') and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        if not state or not user_id:
            return await handler(event, data)
        fsm_data = await state.get_data()
        last_time = fsm_data.get("antispam_last_time")
        now = time.time()
        if last_time and now - last_time < self.delay:
            return  # Игнорируем спам
        await state.update_data(antispam_last_time=now)
        return await handler(event, data) 