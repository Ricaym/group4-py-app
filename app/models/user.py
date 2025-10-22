from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.models._base import Base
from app.models.enums import UserRole

class User(Base):
    """
    Représente un utilisateur de l'application.

    Attributes:
        id (int): L'identifiant unique de l'utilisateur.
        name (str): Le nom de l'utilisateur.
        email (str): L'adresse email de l'utilisateur (doit être unique).
        hashed_password (str): Le mot de passe haché de l'utilisateur.
        role (UserRole): Le rôle de l'utilisateur (par défaut 'abonne').
        created_at (datetime): La date et l'heure de création de l'utilisateur.
        updated_at (datetime): La date et l'heure de la dernière mise à jour de l'utilisateur.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), default=UserRole.USER, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    votes = relationship("Vote", back_populates="user")