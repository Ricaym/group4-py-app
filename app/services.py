from abc import ABC, abstractmethod
import requests
import os
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.activity_instance import ActivityInstance
from app.models.enums import IndoorOutdoor


class WeatherServiceInterface(ABC):
    """
    Interface pour les services météorologiques.
    """
    @abstractmethod
    def get_forecast(self, city: str, date: datetime) -> dict:
        """
        Récupère les prévisions météorologiques pour une ville et une date données.
        """
        pass

class OpenWeatherService(WeatherServiceInterface):
    """
    Implémentation du service météorologique utilisant l'API OpenWeatherMap.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_forecast(self, city: str, date: datetime) -> dict:
        """
        Récupère et agrège les prévisions météorologiques sur 5 jours pour une date spécifique
        depuis OpenWeatherMap.

        Args:
            city (str): Le nom de la ville.
            date (datetime): La date pour laquelle récupérer les prévisions.

        Returns:
            dict: Un dictionnaire contenant les prévisions agrégées pour la journée.

        Raises:
            requests.exceptions.RequestException: Si une erreur survient lors de la requête API.
        """
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        resp = requests.get("https://api.openweathermap.org/data/2.5/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # OpenWeatherMap provides 5-day forecast with data every 3 hours.
        # We need to filter for the specific date and aggregate relevant info.
        daily_forecast = []
        for item in data["list"]:
            forecast_time = datetime.fromtimestamp(item["dt"])
            if forecast_time.date() == date.date():
                daily_forecast.append(item)

        if not daily_forecast:
            return {"message": "Aucune prévision trouvée pour cette date.", "city": city, "date": date.isoformat()}

        # Aggregate data for the day (e.g., average temperature, main weather, humidity, wind)
        avg_temp = sum(item["main"]["temp"] for item in daily_forecast) / len(daily_forecast)
        max_temp = max(item["main"]["temp_max"] for item in daily_forecast)
        min_temp = min(item["main"]["temp_min"] for item in daily_forecast)
        avg_humidity = sum(item["main"]["humidity"] for item in daily_forecast) / len(daily_forecast)
        avg_wind_speed = sum(item["wind"]["speed"] for item in daily_forecast) / len(daily_forecast)
        # Consider the most frequent weather condition description for the day
        weather_descriptions = [item["weather"][0]["description"] for item in daily_forecast]
        main_weather = max(set(weather_descriptions), key=weather_descriptions.count)
        weather_icon = daily_forecast[0]["weather"][0]["icon"]

        # Precipitation (rain/snow) probability - sum of 3-hour precipitation, could be refined
        precipitation = sum(item.get("rain", {}).get("3h", 0) for item in daily_forecast)
        precipitation += sum(item.get("snow", {}).get("3h", 0) for item in daily_forecast)

        return {
            "city": city,
            "date": date.isoformat(),
            "temperature": {"avg": avg_temp, "max": max_temp, "min": min_temp},
            "humidity": avg_humidity,
            "wind_speed": avg_wind_speed,
            "main_weather": main_weather,
            "weather_icon": weather_icon,
            "precipitation": precipitation, # total precipitation for the day
            "details": daily_forecast # Optionally keep detailed 3-hour forecasts
        }


class AQServiceInterface(ABC):
    """
    Interface pour les services de qualité de l'air.
    """
    @abstractmethod
    def get_aq_data(self, city: str, date: datetime) -> dict:
        """
        Récupère les données de qualité de l'air pour une ville et une date données.
        """
        pass

class OpenAQService(AQServiceInterface):
    """
    Implémentation du service de qualité de l'air utilisant l'API OpenAQ.
    """
    def __init__(self):
        # OpenAQ ne nécessite pas de clé API pour les données publiques.
        # Cependant, une gestion des URLs de base est une bonne pratique.
        self.base_url = "https://api.openaq.org/v2/measurements"

    def get_aq_data(self, city: str, date: datetime) -> dict:
        """
        Récupère les données de qualité de l'air (AQI) pour une ville et une date données depuis OpenAQ.
        Note: OpenAQ fournit des mesures plutôt que des prévisions pour une date future.
        Pour une prévision, une intégration plus complexe ou un autre service serait nécessaire.
        Ici, nous simulons une récupération pour la date donnée en cherchant les données disponibles.

        Args:
            city (str): Le nom de la ville.
            date (datetime): La date pour laquelle récupérer les données (utilisée pour filtrer si possible).

        Returns:
            dict: Un dictionnaire contenant l'indice AQI (si disponible) et d'autres données.
        """
        params = {
            "city": city,
            "date_from": date.isoformat(),
            "date_to": (date + timedelta(days=1)).isoformat(), # Cherche sur 24h
            "limit": 100, # Limite le nombre de résultats
            "parameter": "pm25", # Exemple de paramètre, PM2.5 est un bon indicateur d'AQI
            "sort": "desc",
            "order_by": "datetime"
        }
        resp = requests.get(self.base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        aqi_value = None
        if data["results"]:
            # Calculer la moyenne des mesures PM2.5 comme un proxy simple pour l'AQI
            pm25_values = [res["value"] for res in data["results"] if res["parameter"] == "pm25"]
            if pm25_values:
                aqi_value = sum(pm25_values) / len(pm25_values)

        return {
            "city": city,
            "date": date.isoformat(),
            "aqi": aqi_value, # Simplified AQI, could be mapped to a proper scale
            "source": "OpenAQ",
            "raw_data": data # Optionnellement garder les données brutes
        }


class ActivityRepository:
    """
    Dépôt pour l'accès aux données des activités et de leurs instances.
    Fournit des méthodes pour interagir avec la base de données pour les activités.
    """
    def __init__(self, db: Session):
        self.db = db

    def list_for_date(self, date: datetime) -> List[Activity]:
        """
        Liste toutes les activités actives pour une date donnée.

        Args:
            date (datetime): La date pour laquelle les activités sont recherchées.

        Returns:
            List[Activity]: Une liste d'objets Activity actifs à la date spécifiée.
        """
        return (
            self.db.query(Activity)
            .join(ActivityInstance)
            .filter(ActivityInstance.start_dt <= date, ActivityInstance.end_dt >= date)
            .all()
        )

    def list_all(self) -> List[Activity]:
        """
        Liste toutes les activités disponibles dans la base de données.

        Returns:
            List[Activity]: Une liste de tous les objets Activity.
        """
        return self.db.query(Activity).all()
    
    def create_activity(self, activity_data: dict) -> Activity:
        """
        Crée une nouvelle activité dans la base de données.

        Args:
            activity_data (dict): Un dictionnaire contenant les données de la nouvelle activité.

        Returns:
            Activity: L'objet Activity nouvellement créé.
        """
        new_activity = Activity(**activity_data)
        self.db.add(new_activity)
        self.db.commit()
        self.db.refresh(new_activity)
        return new_activity
    
    def create_activity_instance(self, instance_data: dict) -> ActivityInstance:
        """
        Crée une nouvelle instance d'activité dans la base de données.

        Args:
            instance_data (dict): Un dictionnaire contenant les données de la nouvelle instance d'activité.

        Returns:
            ActivityInstance: L'objet ActivityInstance nouvellement créé.
        """
        new_instance = ActivityInstance(**instance_data)
        self.db.add(new_instance)
        self.db.commit()
        self.db.refresh(new_instance)
        return new_instance
