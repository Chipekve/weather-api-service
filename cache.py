import json
import logging
import os
from typing import Optional, Dict, Any, List
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Глобальная переменная для Redis соединения
redis_client: Optional[redis.Redis] = None

# Настройки TTL по умолчанию (в секундах)
DEFAULT_TTL_WEATHER = int(os.getenv("CACHE_TTL_WEATHER", "600"))  # 10 минут
DEFAULT_TTL_FORECAST = int(os.getenv("CACHE_TTL_FORECAST", "1800"))  # 30 минут
DEFAULT_TTL_CITIES = int(os.getenv("CACHE_TTL_CITIES", "3600"))  # 1 час

async def init_redis():
    """Инициализация Redis соединения"""
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # Проверяем соединение
        await redis_client.ping()
        logger.info("Redis соединение установлено успешно")
    except Exception as e:
        logger.warning(f"Не удалось подключиться к Redis: {e}. Кэширование отключено.")
        redis_client = None

async def close_redis():
    """Закрытие Redis соединения"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis соединение закрыто")

def _generate_cache_key(cache_type: str, identifier: str) -> str:
    """Генерация ключа кэша"""
    return f"{cache_type}:{identifier.lower().replace(' ', '_')}"

async def get_cached_data(cache_type: str, identifier: str) -> Optional[Dict[str, Any]]:
    """Получение данных из кэша"""
    if not redis_client:
        return None
    
    try:
        cache_key = _generate_cache_key(cache_type, identifier)
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Данные найдены в кэше: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Ошибка при получении данных из кэша: {e}")
    
    return None

async def set_cached_data(cache_type: str, identifier: str, data: Any, ttl: int) -> bool:
    """Сохранение данных в кэш"""
    if not redis_client:
        return False
    
    try:
        cache_key = _generate_cache_key(cache_type, identifier)
        await redis_client.set(cache_key, json.dumps(data), ex=ttl)
        logger.info(f"Данные сохранены в кэш: {cache_key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в кэш: {e}")
        return False

async def get_weather_cached(city: str) -> Optional[Dict[str, Any]]:
    """Получение погоды с кэшированием"""
    return await get_cached_data("weather", city)

async def set_weather_cached(city: str, data: Dict[str, Any]) -> bool:
    """Сохранение погоды в кэш"""
    return await set_cached_data("weather", city, data, DEFAULT_TTL_WEATHER)

async def get_forecast_cached(city: str) -> Optional[Dict[str, Any]]:
    """Получение прогноза с кэшированием"""
    return await get_cached_data("forecast", city)

async def set_forecast_cached(city: str, data: Dict[str, Any]) -> bool:
    """Сохранение прогноза в кэш"""
    return await set_cached_data("forecast", city, data, DEFAULT_TTL_FORECAST)

async def get_cities_cached(query: str) -> Optional[List[Dict[str, Any]]]:
    """Получение списка городов с кэшированием"""
    cached_data = await get_cached_data("cities", query)
    if cached_data and isinstance(cached_data, list):
        return cached_data
    return None

async def set_cities_cached(query: str, data: List[Dict[str, Any]]) -> bool:
    """Сохранение списка городов в кэш"""
    return await set_cached_data("cities", query, data, DEFAULT_TTL_CITIES)

async def clear_cache(cache_type: Optional[str] = None, identifier: Optional[str] = None) -> bool:
    """Очистка кэша"""
    if not redis_client:
        return False
    
    try:
        if cache_type and identifier:
            # Очистка конкретного ключа
            cache_key = _generate_cache_key(cache_type, identifier)
            await redis_client.delete(cache_key)
            logger.info(f"Кэш очищен: {cache_key}")
        elif cache_type:
            # Очистка всех ключей определенного типа
            pattern = f"{cache_type}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Очищено {len(keys)} ключей типа: {cache_type}")
        else:
            # Очистка всего кэша
            await redis_client.flushdb()
            logger.info("Весь кэш очищен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")
        return False

async def get_cache_stats() -> Dict[str, Any]:
    """Получение статистики кэша"""
    if not redis_client:
        return {"error": "Redis не подключен"}
    
    try:
        info = await redis_client.info()
        keys_count = await redis_client.dbsize()
        return {
            "connected": True,
            "keys_count": keys_count,
            "memory_usage": info.get("used_memory_human", "N/A"),
            "uptime": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статистики кэша: {e}")
        return {"error": str(e)} 