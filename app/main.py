from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.models._base import Base
from app.core import database
from app.routers import activity_router, weather_router, user_router, dashboard_router, vote_router, recommendation_router

Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Météo Activités API")

app.include_router(user_router.router)
app.include_router(dashboard_router.router)
app.include_router(weather_router.router)
app.include_router(activity_router.router)
app.include_router(vote_router.router)
app.include_router(recommendation_router.router)

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Météo Activités !"}
