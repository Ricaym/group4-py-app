from fastapi import FastAPI, Query
from datetime import datetime
from weather_service import WeatherService

app = FastAPI(title="Weather Activity Recommender")

weather_service = WeatherService(api_key="23654828e88ada7b918155c3320f3517")

@app.get("/dashboard")
def get_dashboard(city: str = Query(...), date: str = Query(...)):
    """
    Retourne les données météo + qualité de l'air pour une ville et une date.
    """
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    weather_data = weather_service.get_weather_forecast(city, date_obj)
    
    return {
        "ville": city,
        "date": date,
        "meteo": weather_data,
    }
