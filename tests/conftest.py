"""
Fixtures for tests
"""
import pytest
from fastapi.testclient import TestClient
from main import app
import os
print("WORKING DIR:", os.getcwd())
os.makedirs("data", exist_ok=True)
print("DATA DIR EXISTS:", os.path.exists("data"))


@pytest.fixture
def client():
    """
    Test client fixture for FastAPI application
    """
    return TestClient(app)


@pytest.fixture
def test_weather_data():
    """
    Sample weather data for testing
    """
    return {
        "city": "Moscow",
        "temperature": 20,
        "description": "Clear sky",
        "humidity": 65,
        "wind_speed": 5.5
    } 