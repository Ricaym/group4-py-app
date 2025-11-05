from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models._base import Base

class Profile(Base):
    """
    Représente le profil d'un utilisateur, incluant ses préférences.

    Attributes:
        id (int): L'identifiant unique du profil.
        user_id (int): L'identifiant de l'utilisateur associé à ce profil.
        outdoor_pref (float): Préférence pour les activités de plein air (0 = intérieur seulement, 1 = extérieur préféré).
        children_friendly (bool): Indique si l'utilisateur préfère les activités adaptées aux enfants.
        user (User): L'objet utilisateur associé.
        created_at (datetime): La date et l'heure de création du profil.
        updated_at (datetime): La date et l'heure de la dernière mise à jour du profil.
    """
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    outdoor_pref = Column(Float, default=0.5)  # 0 = indoors only, 1 = outdoors preferred
    children_friendly = Column(Boolean, default=False)
    commute_time = Column(Integer, nullable=True) # temps de trajet en minutes
    activity_intensity_pref = Column(Float, default=0.5) # 0 = faible, 1 = élevée
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")