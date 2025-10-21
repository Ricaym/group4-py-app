from fastapi import FastAPI, Query
from datetime import datetime
from weather_service import WeatherService
from air_service import AirQualityService

app = FastAPI(title="Weather Activity Recommender")

weather_service = WeatherService(api_key="TA_CLE_API_OPENWEATHERMAP")
air_service = AirQualityService(api_key="TA_CLE_API_OPENAQ")

@app.get("/dashboard")
def get_dashboard(city: str = Query(...), date: str = Query(...)):
    """
    Retourne les données météo + qualité de l'air pour une ville et une date.
    """
    # Convertir la date
    date_obj = datetime.strptime(date, "%Y-%m-%d")

    # Appel API météo
    weather_data = weather_service.get_weather_forecast(city, date_obj)
    
    # Appel API qualité de l'air
    air_data = air_service.get_air_quality(city)

    return {
        "ville": city,
        "date": date,
        "meteo": weather_data,
        "qualite_air": air_data
    }
