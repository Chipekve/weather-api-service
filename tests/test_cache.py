import pytest
import json
from cache import _generate_cache_key

def test_generate_cache_key():
    """Тест генерации ключа кэша"""
    key = _generate_cache_key("weather", "Moscow")
    assert key == "weather:moscow"
    
    key = _generate_cache_key("forecast", "New York")
    assert key == "forecast:new_york"
    
    key = _generate_cache_key("cities", "Mosc")
    assert key == "cities:mosc"

@pytest.mark.asyncio
async def test_cache_functions_without_redis():
    """Тест функций кэша без Redis (должны работать gracefully)"""
    from cache import (
        get_weather_cached, set_weather_cached, get_forecast_cached, 
        set_forecast_cached, get_cities_cached, set_cities_cached,
        clear_cache, get_cache_stats
    )
    
    # Тест получения данных без Redis
    result = await get_weather_cached("Moscow")
    assert result is None
    
    # Тест сохранения данных без Redis
    result = await set_weather_cached("Moscow", {"temp": 20})
    assert result is False
    
    # Тест очистки кэша без Redis
    result = await clear_cache()
    assert result is False
    
    # Тест статистики без Redis
    stats = await get_cache_stats()
    assert "error" in stats
    assert stats["error"] == "Redis не подключен"

@pytest.mark.asyncio
async def test_cache_functions_with_mock_redis():
    """Тест функций кэша с моком Redis"""
    from unittest.mock import AsyncMock, patch
    from cache import (
        init_redis, get_weather_cached, set_weather_cached,
        get_cities_cached, set_cities_cached, clear_cache, get_cache_stats
    )
    
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.get.side_effect = [
        json.dumps({"temp": 20, "city": "Moscow"}),  # для get_weather_cached
        json.dumps([{"id": 1, "name": "Moscow"}])   # для get_cities_cached
    ]
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.flushdb.return_value = True
    mock_client.info.return_value = {"used_memory_human": "1.0M", "uptime_in_seconds": 3600}
    mock_client.dbsize.return_value = 5
    
    with patch('cache.redis') as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_client
        
        # Инициализация Redis
        await init_redis()
        
        # Тест получения погоды
        result = await get_weather_cached("Moscow")
        assert result == {"temp": 20, "city": "Moscow"}
        
        # Тест сохранения погоды
        result = await set_weather_cached("Moscow", {"temp": 25})
        assert result is True
        
        # Тест получения городов
        result = await get_cities_cached("Mosc")
        assert result == [{"id": 1, "name": "Moscow"}]
        
        # Тест очистки кэша
        result = await clear_cache("weather", "Moscow")
        assert result is True
        
        # Тест статистики
        stats = await get_cache_stats()
        assert stats["connected"] is True
        assert stats["keys_count"] == 5 