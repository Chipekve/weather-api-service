from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import logging
import sqlite3
from weather_image import generate_weather_image

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather Bot API",
    description="API для работы с погодными данными",
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

# Модели данных
class WeatherRequest(BaseModel):
    user_id: Optional[int] = None
    city: Optional[str] = None
    city_id: Optional[str] = None
    forecast_days: Optional[int] = None

class CitySearchRequest(BaseModel):
    query: str

class WeatherResponse(BaseModel):
    success: bool
    formatted_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CitySearchResponse(BaseModel):
    success: bool
    cities: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class CityListResponse(BaseModel):
    cities: List[Dict[str, Any]]
    has_next: bool

class CityWeatherRequest(BaseModel):
    city: str

# === Работа с БД пользователей ===
DB_PATH = os.getenv("USERS_DB_PATH", "data/users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city_id INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

def set_user_city(user_id: int, city_id: int):
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO users (user_id, city_id) VALUES (?, ?)",
        (user_id, city_id)
    )
    conn.commit()
    conn.close()

def get_user_city(user_id: int) -> Optional[int]:
    conn = get_db_connection()
    cur = conn.execute(
        "SELECT city_id FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row["city_id"] if row else None

# === Модели для новых эндпоинтов ===
class UserStartRequest(BaseModel):
    user_id: int

class CitySearchRequestV2(BaseModel):
    user_id: int
    query: str
    page: int = 1
    page_size: int = 5

class UserCityRequest(BaseModel):
    user_id: int
    city_id: int
    city_name: Optional[str] = None

class SimpleMessageResponse(BaseModel):
    message: str

class StartInfoResponse(BaseModel):
    text: str
    image_url: str

# Конфигурация
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_BASE_URL = "http://api.weatherapi.com/v1"
API_BASE_URL = os.getenv("API_BASE_URL", "http://0.0.0.0:8000")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

IMGUR_URL = "https://imgur.com/vT8VBK5.jpg"
WELCOME_TEXT = (
    "<b>НА туда👉🏼👈🏼</b> сильно похож на <b>НА куда👀</b>\n"
    "Только логика реализована через веб-сервис на FastAPI\n\n"
    "Жми на кнопки ниже, чтобы выбрать город и узнать погоду.\n\n"
    "О работе бота можно узнать по команде /help"
)

if not WEATHER_API_KEY:
    logger.critical("WEATHER_API_KEY не найден в переменных окружения!")

# Функции для работы с WeatherAPI
async def fetch_weather_api(
    city: Optional[str] = None,
    city_id: Optional[str] = None,
    retries: int = 3,
    forecast_days: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Получение данных о погоде от WeatherAPI"""
    if not city and not city_id:
        return None

    params = {
        "key": WEATHER_API_KEY,
        "lang": "ru",
        "q": f"id:{city_id}" if city_id else city,
    }

    endpoint = "current.json"
    if forecast_days:
        endpoint = "forecast.json"
        params["days"] = forecast_days

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{WEATHER_API_BASE_URL}/{endpoint}", params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.warning(f"WeatherAPI вернул статус {response.status}")
        except Exception as e:
            logger.error(f"Ошибка WeatherAPI на попытке {attempt + 1}: {e}")
        await asyncio.sleep(1)
    return None

async def search_cities_api(query: str, retries: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Поиск городов через WeatherAPI"""
    if len(query) < 2:
        return None

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{WEATHER_API_BASE_URL}/search.json",
                    params={"key": WEATHER_API_KEY, "q": query},
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.warning(f"Поиск городов не удался со статусом {response.status}")
        except Exception as e:
            logger.error(f"Ошибка поиска городов на попытке {attempt + 1}: {e}")
        await asyncio.sleep(1)
    return None

# Функции форматирования (перенесены из бота)
async def format_weather(weather: dict) -> str:
    """Форматирование текущей погоды"""
    wind_m_s = round(weather["current"]["wind_kph"] / 3.6, 1)
    return (
        f"🌤 Погода в <b>{weather['location']['name']}</b>:\n"
        f"• 🌡 Температура: <b>{weather['current']['temp_c']}°C</b>\n"
        f"• 🤔 Ощущается как: <b>{weather['current']['feelslike_c']}°C</b>\n"
        f"• 💨 Ветер: <b>{wind_m_s} м/с</b>\n"
        f"• 💧 Влажность: <b>{weather['current']['humidity']}%</b>\n"
        f"• ☁️ Состояние: <b>{weather['current']['condition']['text']}</b>"
    )

async def format_forecast(weather: dict) -> str:
    """Форматирование прогноза погоды"""
    location = weather.get("location", {})
    forecast_days = weather.get("forecast", {}).get("forecastday", [])

    if not location or not forecast_days:
        return "⚠️ Не удалось получить прогноз."

    text = f"📅 Прогноз погоды на 3 дня для <b>{location.get('name')}</b>:\n\n"

    for day in forecast_days:
        date = day.get("date")
        day_info = day.get("day", {})
        condition = day_info.get("condition", {}).get("text", "")
        max_temp = day_info.get("maxtemp_c")
        min_temp = day_info.get("mintemp_c")
        text += (
            f"<b>{date}</b>:\n"
            f"  • Состояние: {condition}\n"
            f"  • Макс: {max_temp}°C, Мин: {min_temp}°C\n\n"
        )
    return text

# Эндпоинты API
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Weather Bot API работает! 🌤️"}

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "api_key_configured": bool(WEATHER_API_KEY)}

@app.post("/weather", response_model=WeatherResponse)
async def get_weather_by_user(request: UserStartRequest):
    city_id = get_user_city(request.user_id)
    if not city_id:
        return WeatherResponse(success=False, error="Сначала выберите город")
    weather_data = await fetch_weather_api(city_id=str(city_id))
    if not weather_data:
        return WeatherResponse(success=False, error="Не удалось получить данные о погоде")
    formatted_message = await format_weather(weather_data)
    return WeatherResponse(success=True, formatted_message=formatted_message, raw_data=weather_data)

@app.post("/cities/search", response_model=CitySearchResponse)
async def search_cities(request: CitySearchRequest):
    """Поиск городов"""
    try:
        cities = await search_cities_api(request.query)
        
        if cities:
            return CitySearchResponse(success=True, cities=cities)
        else:
            return CitySearchResponse(
                success=False, 
                error="Не удалось найти города"
            )
    except Exception as e:
        logger.error(f"Ошибка при поиске городов: {e}")
        return CitySearchResponse(
            success=False, 
            error="Внутренняя ошибка сервера"
        )

@app.get("/weather/current/{city}")
async def get_current_weather(city: str):
    """Получение текущей погоды по городу (GET запрос)"""
    try:
        weather_data = await fetch_weather_api(city=city)
        
        if weather_data:
            formatted_message = await format_weather(weather_data)
            return WeatherResponse(
                success=True, 
                formatted_message=formatted_message,
                raw_data=weather_data
            )
        else:
            raise HTTPException(status_code=404, detail="Город не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении погоды для {city}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/weather/forecast/{city}")
async def get_weather_forecast(city: str, days: int = 3):
    """Получение прогноза погоды по городу (GET запрос)"""
    try:
        weather_data = await fetch_weather_api(city=city, forecast_days=days)
        
        if weather_data:
            formatted_message = await format_forecast(weather_data)
            return WeatherResponse(
                success=True, 
                formatted_message=formatted_message,
                raw_data=weather_data
            )
        else:
            raise HTTPException(status_code=404, detail="Город не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении прогноза для {city}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/user/start", response_model=StartInfoResponse)
async def user_start(request: UserStartRequest):
    return StartInfoResponse(text=WELCOME_TEXT, image_url=IMGUR_URL)

@app.post("/city/search", response_model=CityListResponse)
async def city_search(request: CitySearchRequestV2):
    cities = await search_cities_api(request.query)
    if not cities:
        return {"cities": [], "has_next": False}
    # Пагинация
    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    page_cities = cities[start:end]
    has_next = end < len(cities)
    # Формируем нужные поля: id, name, country
    result = [{"id": c["id"], "name": c["name"], "country": c.get("country", "")} for c in page_cities]
    return {"cities": result, "has_next": has_next}

@app.post("/user/city", response_model=SimpleMessageResponse)
async def user_city(request: UserCityRequest):
    set_user_city(request.user_id, request.city_id)
    return {"message": f"Город выбран!"}

@app.post("/weather/by_city", response_model=WeatherResponse)
async def get_weather_by_city(request: CityWeatherRequest):
    weather_data = await fetch_weather_api(city=request.city)
    if not weather_data:
        return WeatherResponse(success=False, error="Не удалось получить данные о погоде")
    formatted_message = await format_weather(weather_data)
    return WeatherResponse(success=True, formatted_message=formatted_message, raw_data=weather_data)

@app.post("/weather/forecast_by_city", response_model=WeatherResponse)
async def get_forecast_by_city(request: CityWeatherRequest):
    weather_data = await fetch_weather_api(city=request.city, forecast_days=3)
    if not weather_data:
        return WeatherResponse(success=False, error="Не удалось получить прогноз")
    formatted_message = await format_forecast(weather_data)
    return WeatherResponse(success=True, formatted_message=formatted_message, raw_data=weather_data)

@app.post("/weather/image")
async def weather_image(request: UserStartRequest):
    city_id = get_user_city(request.user_id)
    if not city_id:
        return Response(content="Сначала выберите город", media_type="text/plain", status_code=400)
    weather_data = await fetch_weather_api(city_id=str(city_id))
    if not weather_data:
        return Response(content="Ошибка получения погоды", media_type="text/plain", status_code=500)
    city_name = weather_data.get("location", {}).get("name", "Город")
    buf = generate_weather_image(weather_data, city_name)
    return Response(content=buf.read(), media_type="image/png")

@app.post("/weather/image_by_city")
async def weather_image_by_city(request: CityWeatherRequest):
    weather_data = await fetch_weather_api(city=request.city)
    if not weather_data:
        return Response(content="Ошибка получения погоды", media_type="text/plain", status_code=500)
    buf = generate_weather_image(weather_data, request.city)
    return Response(content=buf.read(), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info"
    ) 