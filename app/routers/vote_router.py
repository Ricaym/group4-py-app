# group4-py-app/app/routers/vote_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app import schemas
from app.models.vote import Vote 
from app.models.user import User 
from app.routers.user_router import get_current_user 

router = APIRouter(
    prefix="/votes",
    tags=["votes"],
)

@router.get("/me", response_model=List[schemas.VoteRead])
async def get_my_votes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les votes soumis par l'utilisateur actuellement authentifié.
    """
    votes = db.query(Vote).filter(Vote.user_id == current_user.id).all()
    return votes

@router.get("/{activity_id}", response_model=List[schemas.VoteRead])
async def get_votes_for_activity(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère tous les votes où l'activité_id est présente dans le classement.
    """
    # Utilise la fonction .contains() pour vérifier si l'activity_id est dans la liste ranking
    votes = db.query(Vote).filter(Vote.ranking.contains([activity_id])).all()
    if not votes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun vote trouvé pour cette activité.")
    return votes

@router.post("/", response_model=schemas.VoteRead, status_code=status.HTTP_201_CREATED)
async def create_user_vote(
    vote_data: schemas.VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permet à un utilisateur authentifié de soumettre un vote pour un classement d'activités.
    Un utilisateur peut soumettre un classement. Si un classement existe déjà pour cet utilisateur,
    une erreur est retournée, encourageant l'utilisateur à utiliser la fonction de mise à jour.
    """
    existing_vote = db.query(Vote).filter(
        Vote.user_id == current_user.id
    ).first()

    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà soumis un classement. Veuillez le mettre à jour si vous le souhaitez."
        )
    
    new_vote = Vote(
        user_id=current_user.id,
        ranking=vote_data.ranking
    )
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    return new_vote

@router.put("/{vote_id}", response_model=schemas.VoteRead)
async def update_user_vote(
    vote_id: int,
    vote_update: schemas.VoteCreate, # Réutiliser VoteCreate pour la structure de mise à jour
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour un classement de vote existant de l'utilisateur authentifié.
    """
    db_vote = db.query(Vote).filter(Vote.id == vote_id, Vote.user_id == current_user.id).first()
    if db_vote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote non trouvé ou non autorisé.")

    db_vote.ranking = vote_update.ranking # Met à jour le champ ranking
    
    db.commit()
    db.refresh(db_vote)
    return db_vote

@router.delete("/{vote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_vote(
    vote_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un vote existant de l'utilisateur authentifié.
    """
    db_vote = db.query(Vote).filter(Vote.id == vote_id, Vote.user_id == current_user.id).first()
    if db_vote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote non trouvé ou non autorisé.")

    db.delete(db_vote)
    db.commit()
    return {"message": "Vote supprimé avec succès."}
