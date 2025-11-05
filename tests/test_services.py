import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import requests

from app.services import OpenWeatherService, OpenAQService, ActivityRepository
from app.models import Activity, ActivityInstance, IndoorOutdoor

# Tests pour OpenWeatherService
@patch('app.services.requests.get')
def test_openweather_get_forecast_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "list": [
            {
                "dt": (datetime.now() + timedelta(hours=3)).timestamp(),
                "main": {"temp": 20.0, "temp_max": 22.0, "temp_min": 18.0, "humidity": 60},
                "weather": [{"description": "clear sky", "icon": "01d"}],
                "wind": {"speed": 5.0}
            },
            {
                "dt": (datetime.now() + timedelta(hours=6)).timestamp(),
                "main": {"temp": 21.0, "temp_max": 23.0, "temp_min": 19.0, "humidity": 65},
                "weather": [{"description": "clear sky", "icon": "01d"}],
                "wind": {"speed": 6.0}
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    service = OpenWeatherService("fake_api_key")
    forecast = service.get_forecast("Paris", datetime.now())

    assert forecast["city"] == "Paris"
    assert "temperature" in forecast
    assert forecast["main_weather"] == "clear sky"
    mock_get.assert_called_once()

@patch('app.services.requests.get')
def test_openweather_get_forecast_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("HTTP Error")
    mock_get.return_value = mock_response

    service = OpenWeatherService("fake_api_key")
    with pytest.raises(requests.exceptions.RequestException):
        service.get_forecast("Paris", datetime.now())

# Tests pour OpenAQService
@patch('app.services.requests.get')
def test_openaq_get_aq_data_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"parameter": "pm25", "value": 25.0, "unit": "µg/m³"},
            {"parameter": "pm25", "value": 35.0, "unit": "µg/m³"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    service = OpenAQService()
    aq_data = service.get_aq_data("Paris", datetime.now())

    assert aq_data["city"] == "Paris"
    assert aq_data["aqi"] == 30.0
    mock_get.assert_called_once()

@patch('app.services.requests.get')
def test_openaq_get_aq_data_no_results(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    service = OpenAQService()
    aq_data = service.get_aq_data("Paris", datetime.now())

    assert aq_data["aqi"] is None

# Tests pour ActivityRepository
@pytest.fixture
def mock_db_session():
    return MagicMock()

def test_activity_repo_list_for_date(mock_db_session):
    # Création d'activités fictives
    activity1 = Activity(id=1, title="Course", indoor_outdoor=IndoorOutdoor.OUTDOOR)
    activity2 = Activity(id=2, title="Lecture", indoor_outdoor=IndoorOutdoor.INDOOR)
    activity_instance1 = ActivityInstance(id=1, activity_id=1, start_dt=datetime(2025, 1, 1, 10, 0), end_dt=datetime(2025, 1, 1, 12, 0), activity=activity1)
    activity_instance2 = ActivityInstance(id=2, activity_id=2, start_dt=datetime(2025, 1, 1, 11, 0), end_dt=datetime(2025, 1, 1, 13, 0), activity=activity2)

    # Configuration du mock pour la session db
    mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
        activity1, activity2
    ]

    repo = ActivityRepository(mock_db_session)
    date_to_query = datetime(2025, 1, 1, 11, 30)
    activities = repo.list_for_date(date_to_query)

    assert len(activities) == 2
    assert activities[0].id == 1
    assert activities[1].id == 2

def test_activity_repo_create_activity(mock_db_session):
    activity_data = {"title": "Nage", "description": "", "category": "Sport", "indoor_outdoor": IndoorOutdoor.INDOOR}
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    
    # Simuler le refresh en retournant une nouvelle instance avec un ID
    new_activity_mock = Activity(id=10, **activity_data)
    mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', 10)

    repo = ActivityRepository(mock_db_session)
    new_activity = repo.create_activity(activity_data)

    assert new_activity.title == "Nage"
    assert new_activity.id == 10  # Vérifie que l'ID est défini par le refresh
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(new_activity)
