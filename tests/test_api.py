"""
Tests for API endpoints
"""
import pytest
from fastapi import status


def test_get_weather_success(client):
    """
    Test successful weather request
    """
    response = client.post("/weather/by_city", json={"city": "Moscow"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "raw_data" in data
    assert data["raw_data"] is not None
    assert "current" in data["raw_data"]
    assert "temp_c" in data["raw_data"]["current"]
    assert "condition" in data["raw_data"]["current"]


def test_get_weather_invalid_city(client):
    """
    Test weather request with invalid city
    """
    response = client.post("/weather", json={"user_id": 1, "city": "NonExistentCity123456"})
    # API возвращает 200 с success=False и error, а не 404
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False
    assert data["error"] is not None


def test_search_city(client):
    """
    Test city search functionality
    """
    response = client.post("/cities/search", json={"query": "Mosc"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "cities" in data
    assert isinstance(data["cities"], list)
    assert len(data["cities"]) > 0
    assert any("Moscow" in city.get("name", "") for city in data["cities"])


@pytest.mark.parametrize("invalid_data", [
    {"wrong_field": "Moscow"},
    {},
    {"city": ""},
    {"city": 123},
])
def test_get_weather_invalid_data(client, invalid_data):
    """
    Test weather request with invalid data
    """
    # /weather ожидает user_id и/или city/city_id
    response = client.post("/weather", json=invalid_data)
    assert response.status_code in [
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_400_BAD_REQUEST
    ] 