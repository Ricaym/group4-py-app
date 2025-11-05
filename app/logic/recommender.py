from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services import OpenWeatherService, OpenAQService, ActivityRepository
from app.models import Activity, Profile, User 
from app.models.enums import IndoorOutdoor
from app.core.config import settings

class Recommender:
    """
    Classe responsable de la recommandation d'activités en fonction des prévisions météorologiques
    et du profil utilisateur.
    """
    def __init__(self, db: Session):
        """
        Initialise le Recommender avec la session de base de données.
        Les services sont instanciés ici.

        Args:
            db (Session): La session de base de données SQLAlchemy.
        """
        self.db = db
        self.weather_service = OpenWeatherService(api_key=settings.openweather_api_key)
        self.aq_service = OpenAQService(api_key=settings.openaq_api_key) 
        self.activity_repo = ActivityRepository(db)

    def score_activity(self, activity: Activity, forecast: Dict[str, Any], aq_data: Dict[str, Any], user: User, profile: Profile) -> float:
        """
        Calcule un score pour une activité donnée en fonction des prévisions météorologiques,
        des données de qualité de l'air, du profil utilisateur et des données utilisateur enrichies.

        Args:
            activity (Activity): L'objet activité à évaluer.
            forecast (dict): Les prévisions météorologiques pour la date concernée.
            aq_data (dict): Les données de qualité de l'air pour la date concernée.
            user (User): L'objet utilisateur avec les données enrichies.
            profile (Profile): L'objet profil de l'utilisateur avec les préférences.

        Returns:
            float: Le score de l'activité (plus le score est élevé, mieux c'est).
        """
        base_score = 0.5

        # Préférences intérieures/extérieures du profil
        indoor_outdoor_pref = profile.outdoor_pref
        children_friendly_pref = profile.children_friendly
        commute_time_pref = profile.commute_time
        activity_intensity_pref = profile.activity_intensity_pref

        # Age et Sexe de l'utilisateur
        user_age = user.age
        user_sex = user.sex if user.sex else None # la valeur de l'Enum

        # Logique basée sur les préférences intérieures/extérieures
        if activity.indoor_outdoor == IndoorOutdoor.OUTDOOR:
            base_score += indoor_outdoor_pref * 0.5
        elif activity.indoor_outdoor == IndoorOutdoor.INDOOR:
            base_score += (1 - indoor_outdoor_pref) * 0.5

        # Conditions météorologiques (inchangé)
        temp_avg = forecast.get("temperature", {}).get("avg", 15)
        precipitation = forecast.get("precipitation", 0)
        main_weather = forecast.get("main_weather", "clear sky").lower()
        wind_speed = forecast.get("wind_speed", 0)

        if activity.min_temperature_celsius is not None and temp_avg < activity.min_temperature_celsius:
            base_score -= 0.3
        if activity.max_temperature_celsius is not None and temp_avg > activity.max_temperature_celsius:
            base_score -= 0.3
        if activity.max_wind_speed_kph is not None and wind_speed > activity.max_wind_speed_kph:
            base_score -= 0.4

        if activity.requires_clear_sky and ("rain" in main_weather or "cloud" in main_weather or precipitation > 0.1):
            base_score -= 0.7

        # Qualité de l'air (inchangé)
        aqi = aq_data.get("aqi")
        if aqi is not None:
            if activity.indoor_outdoor == IndoorOutdoor.OUTDOOR:
                if aqi > 100:
                    base_score -= 0.5
                elif aqi < 50:
                    base_score += 0.2
            
            if activity.min_air_quality_index is not None and aqi < activity.min_air_quality_index:
                base_score -= 0.3
            if activity.max_air_quality_index is not None and aqi > activity.max_air_quality_index:
                base_score -= 0.3

        # Logique basée sur l'âge
        if user_age is not None and activity.min_age is not None:
            if user_age < activity.min_age:
                base_score -= 0.4 # Forte pénalité si l'utilisateur est trop jeune
            elif user_age >= activity.min_age + 10: # Bonus si l'activité est bien adaptée à l'âge
                base_score += 0.1

        # Logique basée sur le temps de trajet (exemple simple)
        # Supposons que activity.meta pourrait contenir 'commute_time' pour l'activité
        activity_commute_time = activity.meta.get("commute_time", 0) 
        if commute_time_pref is not None and activity_commute_time > commute_time_pref:
            base_score -= 0.2

        # Logique basée sur l'intensité de l'activité (exemple simple)
        # Supposons que activity.meta pourrait contenir 'intensity' pour l'activité (0.0 à 1.0)
        activity_intensity = activity.meta.get("intensity", 0.5)
        base_score -= abs(activity_intensity - activity_intensity_pref) * 0.3 # Plus la différence est grande, plus la pénalité est forte

        # Activités pour enfants (avec le nouveau champ children_friendly_pref du profil)
        if children_friendly_pref and activity.min_age > 0:
            base_score -= 0.2
        if children_friendly_pref and activity.min_age == 0:
            base_score += 0.1

        return max(0.0, min(1.0, base_score))

    async def get_recommendations(self, user: User, profile: Profile, city: str, date: datetime, limit: int = 10) -> List[Activity]:
        """
        Recommande des activités en fonction de la ville, de la date, du profil et de l'utilisateur.

        Args:
            user (User): L'objet utilisateur.
            profile (Profile): L'objet profil de l'utilisateur.
            city (str): Le nom de la ville.
            date (datetime): La date pour laquelle les recommandations sont faites.
            limit (int): Le nombre maximum d'activités à recommander.

        Returns:
            List[Activity]: Une liste des activités recommandées, triées par score.
        """
        forecast = self.weather_service.get_forecast(city, date)
        aq_data = self.aq_service.get_aq_data(city, date)
        activities = self.activity_repo.list_all()

        scored_activities = []
        for activity in activities:
            score = self.score_activity(activity, forecast, aq_data, user, profile)
            scored_activities.append((score, activity))

        scored_activities.sort(key=lambda x: x[0], reverse=True)

        # Le router attend des objets Activity
        return [activity for score, activity in scored_activities[:limit]]
