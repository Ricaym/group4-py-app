from fastapi import APIRouter, HTTPException, Query, Depends
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

from app.services import OpenWeatherService

router = APIRouter(prefix="/weather", tags=["weather"])

# Dans une vraie application, l'API_KEY devrait être gérée de manière plus sécurisée
# et le service instancié via un système de dépendances de FastAPI.
# Pour l'instant, nous le simplifions pour le développement.'
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
weather_service = OpenWeatherService(OPENWEATHER_API_KEY)

@router.get("/forecast")
def get_weather_forecast(
    city: str = Query(..., description="Nom de la ville"),
    date: str = Query(..., description="Date des prévisions au format YYYY-MM-DD")
):
    """
    Récupère les prévisions météorologiques pour une ville et une date données.

    Args:
        city (str): Le nom de la ville.
        date (str): La date des prévisions au format YYYY-MM-DD.

    Returns:
        dict: Les prévisions météorologiques agrégées pour la journée.

    Raises:
        HTTPException: Si la clé API n'est pas configurée ou si le format de date est invalide.
    """
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "votre_cle_api_openweather":
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY non configurée.")

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD.")

    try:
        forecast_data = weather_service.get_forecast(city, date_obj)
        return forecast_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Erreur de communication avec le service météo: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")
