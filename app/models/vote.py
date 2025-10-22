from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.models._base import Base

class Vote(Base):
    """
    Représente le vote d'un utilisateur pour un classement d'activités.

    Attributes:
        id (int): L'identifiant unique du vote.
        user_id (int): L'identifiant de l'utilisateur qui a voté.
        ranking (JSON): Un classement des activités par ordre de préférence (liste d'IDs d'activités).
        user (User): L'objet utilisateur associé.
        created_at (datetime): La date et l'heure de création du vote.
        updated_at (datetime): La date et l'heure de la dernière mise à jour du vote.
    """
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ranking = Column(JSON, nullable=False)  # e.g. [activity_id1, activity_id3, activity_id2]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="votes")