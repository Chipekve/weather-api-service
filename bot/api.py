import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

async def api_post(endpoint, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}{endpoint}", json=payload) as resp:
            return await resp.json()

async def get_weather_image(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/weather/image", json={"user_id": user_id}) as resp:
            if resp.status == 200:
                return await resp.read()  # возвращаем байты картинки
            else:
                return None

async def get_weather_image_by_city(city):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/weather/image_by_city", json={"city": city}) as resp:
            if resp.status == 200:
                return await resp.read()  # возвращаем байты картинки
            else:
                return None 