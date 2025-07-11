"""
Tests for weather image generation
"""
import os
from PIL import Image
import pytest
from weather_image import generate_weather_image


@pytest.fixture
def test_image_data():
    """
    Sample data for image generation
    """
    return {
        "city": "Moscow",
        "weather_data": {
            "current": {
                "temp_c": 20,
                "condition": {"text": "Clear sky"}
            },
            "location": {
                "localtime": "2024-07-12 12:00"
            }
        }
    }


# Удаляю старый тест с create_weather_image, оставляю только актуальные тесты для generate_weather_image


def test_generate_weather_image(test_image_data):
    """
    Test weather image creation
    """
    buf = generate_weather_image(
        weather_data=test_image_data["weather_data"],
        city=test_image_data["city"]
    )
    # Проверяем, что вернулся BytesIO
    assert hasattr(buf, 'read')
    # Проверяем, что это валидное изображение
    try:
        img = Image.open(buf)
        assert img.size[0] > 0
        assert img.size[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to open generated image: {e}")


@pytest.mark.parametrize("invalid_condition", ["", "invalid", "999", None])
def test_generate_weather_image_invalid_condition(test_image_data, invalid_condition):
    """
    Test weather image creation with invalid condition
    """
    test_image_data["weather_data"]["current"]["condition"]["text"] = invalid_condition
    buf = generate_weather_image(
        weather_data=test_image_data["weather_data"],
        city=test_image_data["city"]
    )
    # Проверяем, что вернулся BytesIO даже при невалидном condition
    assert hasattr(buf, 'read') 