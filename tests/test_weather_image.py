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
        "temperature": 20,
        "description": "Clear sky",
        "humidity": 65,
        "wind_speed": 5.5,
        "icon": "01d"
    }


def test_create_weather_image(test_image_data):
    """
    Test weather image creation
    """
    image_path = create_weather_image(
        city=test_image_data["city"],
        temperature=test_image_data["temperature"],
        description=test_image_data["description"],
        humidity=test_image_data["humidity"],
        wind_speed=test_image_data["wind_speed"],
        icon=test_image_data["icon"]
    )
    
    # Проверяем, что файл создан
    assert os.path.exists(image_path)
    
    # Проверяем, что это валидное изображение
    try:
        with Image.open(image_path) as img:
            assert img.size[0] > 0
            assert img.size[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to open generated image: {e}")
    finally:
        # Удаляем тестовое изображение
        if os.path.exists(image_path):
            os.remove(image_path)


@pytest.mark.parametrize("invalid_icon", ["", "invalid", "999", None])
def test_create_weather_image_invalid_icon(test_image_data, invalid_icon):
    """
    Test weather image creation with invalid icon
    """
    test_image_data["icon"] = invalid_icon
    with pytest.raises(Exception):
        create_weather_image(
            city=test_image_data["city"],
            temperature=test_image_data["temperature"],
            description=test_image_data["description"],
            humidity=test_image_data["humidity"],
            wind_speed=test_image_data["wind_speed"],
            icon=test_image_data["icon"]
        ) 