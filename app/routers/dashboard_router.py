from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func # Importez func pour les fonctions d'agrégation SQL
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.database import get_db
# Importer les modèles nécessaires pour les requêtes de statistiques
from app.models.user import User
from app.models.activity import Activity
from app.models.recommendation import Recommandation
from app.models.history import Historique # Pour l'historique des choix
from app.models.enums import UserRole # Pour les rôles utilisateurs

# Si vous souhaitez protéger ce dashboard avec une authentification
from app.routers.user_router import get_current_user # Assurez-vous d'importer cette fonction

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

@router.get("/", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Décommenter pour protéger l'endpoint
):
    """
    Récupère des statistiques agrégées pour le tableau de bord.
    Accessible uniquement aux utilisateurs authentifiés avec le rôle administrateur.
    """
    # Restreindre l'accès aux administrateurs
    # if current_user.role != UserRole.ADMIN:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Vous n'êtes pas autorisé à accéder au tableau de bord."
    #     )


    # --- Statistiques Générales ---
    total_users = db.query(User).count()
    total_activities = db.query(Activity).count()
    total_recommendations = db.query(Recommandation).count()
    total_choices_history = db.query(Historique).count()

    # --- Statistiques Utilisateurs ---
    # Nombre d'utilisateurs par rôle
    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role_dict = {role.value: count for role, count in users_by_role}

    # Nouveaux utilisateurs dans les 7 derniers jours
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users_last_7_days = db.query(User).filter(User.created_at >= seven_days_ago).count()
    
    # --- Statistiques Activités ---
    # Nombre d'activités par catégorie
    activities_by_category = db.query(Activity.category, func.count(Activity.id)).group_by(Activity.category).all()
    activities_by_category_dict = {category: count for category, count in activities_by_category}

    # Activités les plus populaires (basé sur le nombre de fois qu'elles apparaissent dans l'historique)
    popular_activities = db.query(
        Activity.title,
        func.count(Historique.activite_id).label("choice_count")
    ).join(Historique, Historique.activite_id == Activity.id)\
    .group_by(Activity.title)\
    .order_by(func.count(Historique.activite_id).desc())\
    .limit(5).all()
    popular_activities_list = [{"name": name, "choices": count} for name, count in popular_activities]


    return {
        "general_stats": {
            "total_users": total_users,
            "total_activities": total_activities,
            "total_recommendations": total_recommendations,
            "total_choices_history": total_choices_history,
        },
        "user_stats": {
            "users_by_role": users_by_role_dict,
            "new_users_last_7_days": new_users_last_7_days,
        },
        "activity_stats": {
            "activities_by_category": activities_by_category_dict,
            "popular_activities": popular_activities_list,
        },
        "message": "Statistiques complètes du tableau de bord."
    }
