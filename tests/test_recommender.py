from datetime import datetime
from unittest.mock import MagicMock

from app.logic.recommender import Recommender
from app.models.models import Activity, IndoorOutdoor

def test_recommender_basic_recommendation():
    # Mocks pour les dépendances
    mock_weather_service = MagicMock()
    mock_aq_service = MagicMock()
    mock_activity_repo = MagicMock()

    # Configuration des retours des mocks
    mock_weather_service.get_forecast.return_value = {
        "city": "TestCity",
        "date": "2025-10-27T00:00:00",
        "temperature": {"avg": 20.0, "max": 25.0, "min": 15.0},
        "humidity": 60.0,
        "wind_speed": 10.0,
        "main_weather": "clear sky",
        "weather_icon": "01d",
        "precipitation": 0.0
    }
    mock_aq_service.get_aq_data.return_value = {"city": "TestCity", "date": "2025-10-27T00:00:00", "aqi": 30.0}
    
    # Création d'activités fictives
    activity1 = Activity(id=1, title="Randonnée", description="", category="Plein air", indoor_outdoor=IndoorOutdoor.OUTDOOR,
                         min_temperature_celsius=10, max_temperature_celsius=30, max_wind_speed_kph=20, requires_clear_sky=True,
                         min_air_quality_index=0, max_air_quality_index=50)
    activity2 = Activity(id=2, title="Musée", description="", category="Culture", indoor_outdoor=IndoorOutdoor.INDOOR,
                         min_temperature_celsius=0, max_temperature_celsius=40)

    mock_activity_repo.list_for_date.return_value = [activity1, activity2]

    recommender = Recommender(mock_weather_service, mock_aq_service, mock_activity_repo)
    
    # Profil utilisateur par défaut
    user_profile = {"outdoor_pref": 0.7, "children_friendly": False}
    
    date_obj = datetime(2025, 10, 27)
    recommendations = recommender.recommend("TestCity", date_obj, user_profile)

    assert len(recommendations) == 2
    assert recommendations[0]["id"] == 1  # Randonnée devrait être préférée
    assert recommendations[1]["id"] == 2

    mock_weather_service.get_forecast.assert_called_once_with("TestCity", date_obj)
    mock_aq_service.get_aq_data.assert_called_once_with("TestCity", date_obj)
    mock_activity_repo.list_for_date.assert_called_once_with(date_obj)
