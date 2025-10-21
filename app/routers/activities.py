from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from pydantic import BaseModel, Field

from app import models, database
from app.services import OpenWeatherService, OpenAQService, ActivityRepository
from app.recommender import Recommender
import os

router = APIRouter(prefix="/activities", tags=["activities"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_activity_repository(db: Session = Depends(get_db)) -> ActivityRepository:
    return ActivityRepository(db)

def get_weather_service() -> OpenWeatherService:
    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key.strip() == "":
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY non configurée.")
    return OpenWeatherService(api_key)

def get_aq_service() -> OpenAQService:
    return OpenAQService()


class ActivityBase(BaseModel):
    title: str = Field(..., example="Randonnée en forêt")
    description: Optional[str] = Field(None, example="Une belle randonnée pour toute la famille.")
    category: Optional[str] = Field(None, example="Plein air")
    indoor_outdoor: models.IndoorOutdoor = Field(models.IndoorOutdoor.MIX, example="outdoor")
    min_age: Optional[int] = Field(0, example=6)
    min_temperature_celsius: Optional[float] = Field(None, example=10.0)
    max_temperature_celsius: Optional[float] = Field(None, example=25.0)
    max_wind_speed_kph: Optional[float] = Field(None, example=20.0)
    requires_clear_sky: bool = Field(False, example=True)
    min_air_quality_index: Optional[int] = Field(None, example=0)
    max_air_quality_index: Optional[int] = Field(None, example=50)

class ActivityCreate(ActivityBase):
    pass

class ActivityRead(ActivityBase):
    id: int
    average_rating: float
    votes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ActivityInstanceBase(BaseModel):
    activity_id: int = Field(..., example=1)
    start_dt: datetime = Field(..., example="2025-10-27T10:00:00Z")
    end_dt: datetime = Field(..., example="2025-10-27T12:00:00Z")
    location: Optional[str] = Field(None, example="Forêt de Fontainebleau")

class ActivityInstanceCreate(ActivityInstanceBase):
    pass

class ActivityInstanceRead(ActivityInstanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@router.get("", response_model=List[ActivityRead])
def list_activities(activity_repo: ActivityRepository = Depends(get_activity_repository)):
    """
    Récupère la liste complète des activités disponibles.
    """
    activities = activity_repo.list_all()
    return activities


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(activity: ActivityCreate, activity_repo: ActivityRepository = Depends(get_activity_repository)):
    """
    Crée une nouvelle activité (réservée à l'administrateur).
    """
    new_activity_data = activity.dict()
    new_activity = activity_repo.create_activity(new_activity_data)
    return new_activity


@router.post("/instances", response_model=ActivityInstanceRead, status_code=status.HTTP_201_CREATED)
def create_activity_instance(
    instance: ActivityInstanceCreate,
    activity_repo: ActivityRepository = Depends(get_activity_repository)
):
    """
    Crée une nouvelle instance d'activité (réservée à l'administrateur).
    """
    instance_data = instance.dict()
    new_instance = activity_repo.create_activity_instance(instance_data)
    return new_instance


@router.get("/by-date", response_model=List[ActivityRead])
def get_activities_by_date(
    date: str = Query(..., description="Date au format YYYY-MM-DD"),
    activity_repo: ActivityRepository = Depends(get_activity_repository),
):
    """
    Récupère les activités prévues à une date donnée (ActivityInstance).
    """
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilise YYYY-MM-DD")

    activities = activity_repo.list_for_date(datetime.combine(date_obj, datetime.min.time()))
    return activities


@router.get("/recommendations", response_model=List[ActivityRead])
def recommend_activities(
    city: str = Query(..., example="Paris"),
    date: str = Query(..., description="Date au format YYYY-MM-DD", example="2025-10-27"),
    user_id: Optional[int] = Query(None, description="ID de l'utilisateur pour des recommandations personnalisées."),
    db: Session = Depends(get_db),
    weather_service: OpenWeatherService = Depends(get_weather_service),
    aq_service: OpenAQService = Depends(get_aq_service),
    activity_repo: ActivityRepository = Depends(get_activity_repository)
):
    """
    Recommande des activités selon la météo et le profil utilisateur.
    
    Args:
        city (str): La ville pour laquelle obtenir les prévisions.
        date (str): La date au format YYYY-MM-DD.
        user_id (Optional[int]): L'ID de l'utilisateur pour obtenir son profil.
        db (Session): La session de base de données.
        weather_service (OpenWeatherService): Le service de prévisions météorologiques.
        aq_service (OpenAQService): Le service de qualité de l'air.
        activity_repo (ActivityRepository): Le dépôt d'activités.
        
    Returns:
        List[ActivityRead]: Une liste des activités recommandées.

    Raises:
        HTTPException: Si le format de date est invalide ou si l'API météo n'est pas configurée.
    """
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")

    profile_data: Dict[str, Any] = {"outdoor_pref": 0.5, "children_friendly": False} # Profil par défaut
    if user_id:
        user_profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
        if user_profile:
            profile_data["outdoor_pref"] = user_profile.outdoor_pref
            profile_data["children_friendly"] = user_profile.children_friendly

    recommender = Recommender(weather_service, aq_service, activity_repo)
    recs = recommender.recommend(city, date_obj, profile_data)
    return recs
