
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import RecommendationRequest, RecommendationResponse, ActivityRead
from app.logic.recommender import Recommender
from app.routers.user_router import get_current_user
from app.models.user import User
from app.models.profile import Profile

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

@router.post("/", response_model=List[ActivityRead])
async def get_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère une liste d'activités recommandées pour l'utilisateur actuel
    en fonction de ses préférences et des conditions météorologiques.
    """
    # Assurez-vous que l'utilisateur a un profil
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil utilisateur non trouvé.")

    # Initialiser le Recommender avec la session DB
    recommender = Recommender(db)

    # Obtenir les recommandations
    recommended_activities = await recommender.get_recommendations(
        user=current_user,
        profile=profile,
        city=request.city,
        date=request.date
    )

    return recommended_activities
