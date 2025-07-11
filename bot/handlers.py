from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from .keyboards import main_kb, get_cities_keyboard, PAGE_SIZE, TEXT_SET_CITY, TEXT_WEATHER, TEXT_SHOW_CITY, CANCEL_KB, CANCEL_TEXT, get_popular_cities_keyboard, get_weather_image_keyboard, SHOW_IMAGE_CALLBACK
from .states import CitySelectStates
from .api import api_post, get_weather_image, get_weather_image_by_city
import asyncio
from rich import print as rich_print
from aiogram.filters import ExceptionTypeFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.types.input_file import BufferedInputFile
from aiogram.types import InputMediaPhoto

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    print("DEBUG TEXT_WEATHER:", TEXT_WEATHER)
    print("DEBUG main_kb:", main_kb)
    info = await api_post("/user/start", {"user_id": message.from_user.id})
    text = info.get("text")
    video_url = "https://i.imgur.com/LJdfKwu.mp4"
    if text:
        await message.answer_animation(animation=video_url, caption=text, reply_markup=main_kb)
    else:
        await message.answer("Ошибка: не удалось получить приветствие.", reply_markup=main_kb)

@router.message(F.text == TEXT_SET_CITY)
async def set_city_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cancel_msg_id = data.get("cancel_msg_id")
    prev_user_msg_id = data.get("user_msg_id")
    try:
        if cancel_msg_id:
            await message.bot.delete_message(message.chat.id, cancel_msg_id)
    except Exception:
        pass
    try:
        if prev_user_msg_id:
            await message.bot.delete_message(message.chat.id, prev_user_msg_id)
    except Exception:
        pass
    user_id = message.from_user.id
    await state.update_data(user_msg_id=message.message_id)
    sent = await message.answer(
        "Введите название города:",
        reply_markup=CANCEL_KB
    )
    await state.set_state(CitySelectStates.waiting_for_city_name)
    await state.update_data(cancel_msg_id=sent.message_id)

@router.callback_query(F.data == "cancel_city", CitySelectStates.waiting_for_city_name)
async def cancel_city_handler(callback: types.CallbackQuery, state: FSMContext):
    rich_print(f"[green]Callback: {callback.data} от пользователя {callback.from_user.id}[/green]")
    await callback.answer("OK")
    if not callback.message:
        await state.clear()
        await state.update_data(cancel_msg_id=None)
        return
    fsm_data = await state.get_data()
    cancel_msg_id = fsm_data.get("cancel_msg_id")
    chat_id = callback.message.chat.id
    bot = callback.message.bot
    if cancel_msg_id:
        try:
            await bot.edit_message_text(
                text="❌Смена города прервана",
                chat_id=chat_id,
                message_id=cancel_msg_id
            )
            await asyncio.sleep(1)
            await bot.delete_message(chat_id, cancel_msg_id)
        except Exception:
            pass
    else:
        # fallback: если cancel_msg_id нет, отправить обычное сообщение
        cancel_msg = await bot.send_message(chat_id, "❌Смена города прервана")
        await asyncio.sleep(1)
        try:
            await bot.delete_message(chat_id, cancel_msg.message_id)
        except Exception:
            pass
    await state.clear()
    await state.update_data(cancel_msg_id=None)

@router.message(CitySelectStates.waiting_for_city_name)
async def city_search_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    # Если пользователь нажал основную кнопку — сбрасываем FSM и вызываем нужный хэндлер
    if text in [TEXT_WEATHER, TEXT_SHOW_CITY, TEXT_SET_CITY, "Популярные города", "/start", "/help"]:
        fsm_data = await state.get_data()
        cancel_msg_id = fsm_data.get("cancel_msg_id")
        if cancel_msg_id:
            try:
                await message.bot.edit_message_text(
                    text="❌Смена города прервана",
                    chat_id=message.chat.id,
                    message_id=cancel_msg_id
                )
                await asyncio.sleep(1)
                await message.bot.delete_message(message.chat.id, cancel_msg_id)
            except Exception:
                pass
        else:
            # fallback: если cancel_msg_id нет, отправить обычное сообщение
            cancel_msg = await message.answer("❌Смена города прервана")
            await asyncio.sleep(1)
            try:
                await cancel_msg.delete()
            except Exception:
                pass
        await state.clear()
        # Только после удаления сообщения вызываем нужный хэндлер
        if text == TEXT_WEATHER:
            await weather_handler(message, state)
        elif text == TEXT_SHOW_CITY:
            await show_city_handler(message, state)
        elif text == TEXT_SET_CITY:
            await set_city_start(message, state)
        elif text == "Популярные города":
            await popular_cities_handler(message, state)
        elif text == "/start":
            await cmd_start(message, state)
        elif text == "/help":
            await help_handler(message, state)
        return
    # ... остальная логика поиска города ...
    query = text
    page = 1
    data = await api_post("/city/search", {"user_id": user_id, "query": query, "page": page, "page_size": PAGE_SIZE})
    cities = data.get("cities", [])
    has_next = data.get("has_next", False)
    if not cities:
        await message.answer("Города не найдены. Попробуйте ещё раз.")
        return
    kb = get_cities_keyboard(cities, has_next, page, query)
    fsm_data = await state.get_data()
    cancel_msg_id = fsm_data.get("cancel_msg_id")
    if cancel_msg_id:
        try:
            await message.bot.edit_message_text(
                text="Выберите город:",
                chat_id=message.chat.id,
                message_id=cancel_msg_id,
                reply_markup=kb
            )
        except Exception:
            sent = await message.answer("Выберите город:", reply_markup=kb)
            await state.update_data(cancel_msg_id=sent.message_id)
    else:
        sent = await message.answer("Выберите город:", reply_markup=kb)
        await state.update_data(cancel_msg_id=sent.message_id)

@router.callback_query(F.data.startswith("city_"), CitySelectStates.waiting_for_city_name)
async def city_choose_handler(callback: types.CallbackQuery, state: FSMContext):
    rich_print(f"[green]Callback: {callback.data} от пользователя {callback.from_user.id}[/green]")
    await callback.answer("OK")
    user_id = callback.from_user.id
    parts = callback.data.split("_", 3)
    city_id = int(parts[1])
    page = int(parts[2])
    query = parts[3]
    await api_post("/user/city", {"user_id": user_id, "city_id": city_id})
    data = await api_post("/city/search", {"user_id": user_id, "query": query, "page": page, "page_size": PAGE_SIZE})
    cities = data.get("cities", [])
    city_name = next((c["name"] for c in cities if int(c["id"]) == city_id), None)
    if city_name:
        await callback.message.edit_text(f"{city_name} — 👀 я это запишу ✍️", reply_markup=None)
    else:
        await callback.message.edit_text("Город выбран!", reply_markup=None)
    await state.clear()
    await asyncio.sleep(1)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.update_data(cancel_msg_id=None)
    weather = await api_post("/weather", {"user_id": user_id})
    if weather.get("success"):
        await callback.message.answer(
            weather["formatted_message"],
            reply_markup=get_weather_image_keyboard()
        )
    else:
        await callback.message.answer(
            weather.get("error", "Ошибка получения погоды")
        )

@router.callback_query(F.data.startswith("page_"), CitySelectStates.waiting_for_city_name)
async def city_pagination_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("OK")
    user_id = callback.from_user.id
    parts = callback.data.split("_", 2)
    page = int(parts[1])
    query = parts[2]
    data = await api_post("/city/search", {"user_id": user_id, "query": query, "page": page, "page_size": PAGE_SIZE})
    cities = data.get("cities", [])
    has_next = data.get("has_next", False)
    kb = get_cities_keyboard(cities, has_next, page, query)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.message(F.text == TEXT_WEATHER)
async def weather_handler(message: types.Message, state: FSMContext):
    await state.clear()
    rich_print(f"[green]Погода: пользователь {message.from_user.id} запросил погоду[/green]")
    user_id = message.from_user.id
    data = await api_post("/weather", {"user_id": user_id})
    if data.get("success"):
        await message.answer(
            data["formatted_message"],
            reply_markup=get_weather_image_keyboard()
        )
    else:
        await message.answer(data.get("error", "Ошибка получения погоды"))

@router.message(F.text == TEXT_SHOW_CITY)
async def show_city_handler(message: types.Message, state: FSMContext):
    await state.clear()
    rich_print(f"[green]Узнать город: пользователь {message.from_user.id} запросил свой город[/green]")
    user_id = message.from_user.id
    # Получаем город из API
    data = await api_post("/weather", {"user_id": user_id})
    if data.get("success") and data.get("raw_data"):
        city = data["raw_data"].get("location", {}).get("name")
        country = data["raw_data"].get("location", {}).get("country")
        if city and country:
            await message.answer(f"Твой город: {city}, {country}")
        elif city:
            await message.answer(f"Твой город: {city}")
        else:
            await message.answer("Город не выбран. Сначала выберите город.")
    else:
        await message.answer("Город не выбран. Сначала выберите город.")

@router.message(F.text == "/help")
async def help_handler(message: types.Message, state: FSMContext):
    await state.clear()
    help_text = (
        "Этот бот — современный интерфейс и демонстрация работы с веб-сервисом на FastAPI.\n\n"
        "<i>Вся логика, хранение данных и интеграции вынесены на сервер.</i>\n\n"
        "<b>Почему так лучше?</b>\n"
        "• <b>⚡ Скорость</b> — все вычисления и хранение данных происходят на сервере, бот всегда быстрый и отзывчивый.\n"
        "• <b>🔄 Масштабируемость</b> — легко подключать новых пользователей и расширять функционал без изменений в самом боте.\n"
        "• <b>🛠 Гибкость</b> — бизнес-логику, интеграции и аналитику можно развивать на стороне сервиса, не трогая Telegram.\n\n"
        "<b>Как это работает?</b>\n"
        "1. Ты выбираешь город — бот отправляет запрос на сервер.\n"
        "2. Сервер ищет город, хранит твой выбор, получает погоду и возвращает готовый ответ.\n"
        "3. Бот просто красиво показывает результат и клавиатуру.\n\n"
        "<b>Пример использования:</b>\n"
        "<i>Можно интегрировать этот сервис в:</i>\n"
        "• <i>мобильное приложение (iOS, Android)</i>\n"
        "• <i>десктопную программу (Windows, macOS)</i>\n"
        "• <i>бота для Telegram или любого другого мессенджера</i>\n"
        "• <i>сайт или внутренний сервис</i>\n"
        "Все эти клиенты могут использовать API одновременно.\n\n"
        "<b>💡 Особенности:</b>\n"
        "• Не нужно хранить данные в Telegram — всё централизовано и безопасно.\n"
        "• Можно быстро добавлять новые функции (например, прогноз, уведомления, аналитику).\n\n"
    )
    await message.answer(help_text)
    gif_url = "https://i.imgur.com/M2tKCc3.mp4"
    await message.answer_animation(gif_url)

@router.message(F.text == "Популярные города")
async def popular_cities_handler(message: types.Message, state: FSMContext):
    await state.clear()
    rich_print(f"[green]Популярные города: пользователь {message.from_user.id} запросил список[/green]")
    kb = get_popular_cities_keyboard(page=1)
    await message.answer("Выберите город из списка:", reply_markup=kb)

@router.callback_query(F.data.startswith("popularcity_"))
async def popular_city_weather_handler(callback: types.CallbackQuery):
    city = callback.data[len("popularcity_"):].strip()
    rich_print(f"[green]Популярный город: пользователь {callback.from_user.id} выбрал {city}[/green]")
    await callback.answer("OK")
    # Получаем погоду по названию города (через POST /weather/by_city)
    data = await api_post("/weather/by_city", {"city": city})
    if data.get("success"):
        await callback.message.edit_text(
            data["formatted_message"],
            reply_markup=get_weather_image_keyboard(city)
        )
    else:
        await callback.message.edit_text(data.get("error", "Ошибка получения погоды"))

@router.callback_query(F.data.startswith("popularpage_"))
async def popular_cities_pagination_handler(callback: types.CallbackQuery):
    page = int(callback.data[len("popularpage_"):])
    await callback.answer("OK")
    kb = get_popular_cities_keyboard(page=page)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("popularforecast_"))
async def popular_city_forecast_handler(callback: types.CallbackQuery):
    city = callback.data[len("popularforecast_"):].strip()
    rich_print(f"[green]Популярный город: пользователь {callback.from_user.id} запросил прогноз по {city}[/green]")
    await callback.answer("OK")
    # Получаем прогноз по названию города (через POST /weather/forecast_by_city)
    data = await api_post("/weather/forecast_by_city", {"city": city})
    if data.get("success"):
        await callback.message.edit_text(data["formatted_message"])
    else:
        await callback.message.edit_text(data.get("error", "Ошибка получения прогноза"))

@router.callback_query()
async def show_weather_image_handler(callback: types.CallbackQuery):
    if callback.data.startswith(SHOW_IMAGE_CALLBACK):
        user_id = callback.from_user.id
        await callback.answer("OK")
        if callback.data.startswith(f"{SHOW_IMAGE_CALLBACK}:"):
            city = callback.data.split(":", 1)[1]
            image_bytes = await get_weather_image_by_city(city)
        else:
            image_bytes = await get_weather_image(user_id)
        if image_bytes:
            image_file = BufferedInputFile(image_bytes, filename="weather.png")
            try:
                await callback.message.edit_media(InputMediaPhoto(media=image_file))
            except Exception as e:
                await callback.message.answer_photo(image_file)
        else:
            await callback.message.answer("Не удалось получить картинку погоды.")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

@router.callback_query()
async def log_any_callback(callback: types.CallbackQuery):
    rich_print(f"[green]Callback: {callback.data} от пользователя {callback.from_user.id}[/green]")
    await callback.answer("OK") 