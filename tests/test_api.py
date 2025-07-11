"""
Tests for API endpoints
"""
import pytest
from fastapi import status


def test_get_weather_success(client, test_weather_data):
    """
    Test successful weather request
    """
    response = client.post("/weather", json={"city": "Moscow"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "temperature" in data
    assert "description" in data
    assert "humidity" in data
    assert "wind_speed" in data


def test_get_weather_invalid_city(client):
    """
    Test weather request with invalid city
    """
    response = client.post("/weather", json={"city": "NonExistentCity123456"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_search_city(client):
    """
    Test city search functionality
    """
    response = client.post("/cities/search", json={"query": "Mosc"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any("Moscow" in city for city in data)


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
    response = client.post("/weather", json=invalid_data)
    assert response.status_code in [
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_400_BAD_REQUEST
    ] 