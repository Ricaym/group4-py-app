from typing import List, Dict, Any
from datetime import datetime

from app.services import WeatherServiceInterface, AQServiceInterface
from app.models import Activity, Profile # Assurez-vous d'importer Profile si ce n'est pas déjà fait

class Recommender:
    """
    Classe responsable de la recommandation d'activités en fonction des prévisions météorologiques
    et du profil utilisateur.
    """
    def __init__(self, weather_service: WeatherServiceInterface, aq_service: AQServiceInterface, activity_repo):
        """
        Initialise le Recommender avec les services et dépôts nécessaires.

        Args:
            weather_service (WeatherServiceInterface): Service pour obtenir les prévisions météorologiques.
            aq_service (AQServiceInterface): Service pour obtenir les données de qualité de l'air.
            activity_repo: Dépôt pour accéder aux activités.
        """
        self.weather_service = weather_service
        self.aq_service = aq_service
        self.activity_repo = activity_repo

    def score_activity(self, activity: Activity, forecast: Dict[str, Any], aq_data: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """
        Calcule un score pour une activité donnée en fonction des prévisions météorologiques,
        des données de qualité de l'air et du profil utilisateur.

        Args:
            activity (Activity): L'objet activité à évaluer.
            forecast (dict): Les prévisions météorologiques pour la date concernée.
            aq_data (dict): Les données de qualité de l'air pour la date concernée.
            profile (dict): Le profil de l'utilisateur (par exemple, préférences plein air).

        Returns:
            float: Le score de l'activité (plus le score est élevé, mieux c'est).
        """
        base_score = 0.5
        indoor_outdoor_pref = profile.get("outdoor_pref", 0.5)
        children_friendly_pref = profile.get("children_friendly", False)

        # Préférences intérieures/extérieures
        if activity.indoor_outdoor.value == "outdoor":
            base_score += indoor_outdoor_pref * 0.5  # Augmente le score si l'utilisateur préfère l'extérieur
        elif activity.indoor_outdoor.value == "indoor":
            base_score += (1 - indoor_outdoor_pref) * 0.5 # Augmente le score si l'utilisateur préfère l'intérieur

        # Conditions météorologiques
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
            base_score -= 0.7 # Pénalité significative si ciel dégagé requis et conditions mauvaises

        # Qualité de l'air
        aqi = aq_data.get("aqi")
        if aqi is not None:
            if activity.indoor_outdoor.value == "outdoor":
                if aqi > 100:
                    base_score -= 0.5 # Pénalise fortement les activités extérieures en cas de mauvaise qualité de l'air
                elif aqi < 50:
                    base_score += 0.2 # Bonus pour bonne qualité de l'air pour les activités extérieures
            
            if activity.min_air_quality_index is not None and aqi < activity.min_air_quality_index:
                base_score -= 0.3
            if activity.max_air_quality_index is not None and aqi > activity.max_air_quality_index:
                base_score -= 0.3

        # Activités pour enfants
        if children_friendly_pref and activity.min_age > 0:
            base_score -= 0.2 # Pénalise légèrement si l'utilisateur préfère des activités pour enfants mais l'activité a un âge minimum
        if children_friendly_pref and activity.min_age == 0:
            base_score += 0.1 # Bonus pour les activités adaptées aux enfants si l'utilisateur le souhaite

        # Normalisation et limites (le score ne peut pas être négatif)
        return max(0.0, min(1.0, base_score))

    def recommend(self, city: str, date: datetime, user_profile: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recommande des activités en fonction de la ville, de la date, du profil utilisateur
        et des conditions météorologiques et de qualité de l'air.

        Args:
            city (str): Le nom de la ville.
            date (datetime): La date pour laquelle les recommandations sont faites.
            user_profile (dict): Le profil de l'utilisateur.
            limit (int): Le nombre maximum d'activités à recommander.

        Returns:
            List[Dict[str, Any]]: Une liste des activités recommandées, triées par score.
        """
        forecast = self.weather_service.get_forecast(city, date)
        aq_data = self.aq_service.get_aq_data(city, date)
        activities = self.activity_repo.list_for_date(date)

        scored_activities = []
        for activity in activities:
            score = self.score_activity(activity, forecast, aq_data, user_profile)
            scored_activities.append((score, activity))

        scored_activities.sort(key=lambda x: x[0], reverse=True)

        # Convertir les objets Activity en dictionnaires pour la réponse de l'API
        return [self._activity_to_dict(activity) for score, activity in scored_activities[:limit]]

    def _activity_to_dict(self, activity: Activity) -> Dict[str, Any]:
        """
        Convertit un objet Activity en dictionnaire pour la sérialisation JSON.
        """
        return {
            "id": activity.id,
            "title": activity.title,
            "description": activity.description,
            "category": activity.category,
            "indoor_outdoor": activity.indoor_outdoor.value,
            "min_age": activity.min_age,
            "min_temperature_celsius": activity.min_temperature_celsius,
            "max_temperature_celsius": activity.max_temperature_celsius,
            "max_wind_speed_kph": activity.max_wind_speed_kph,
            "requires_clear_sky": activity.requires_clear_sky,
            "min_air_quality_index": activity.min_air_quality_index,
            "max_air_quality_index": activity.max_air_quality_index,
            "average_rating": activity.average_rating,
            "votes": activity.votes,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "updated_at": activity.updated_at.isoformat() if activity.updated_at else None,
            # Ajoutez d'autres champs si nécessaire
        }
