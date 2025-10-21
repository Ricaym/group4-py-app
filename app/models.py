import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class IndoorOutdoor(enum.Enum):
    """
    Représente si une activité est en intérieur, en extérieur ou un mélange des deux.
    """
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIX = "mix"

class UserRole(enum.Enum):
    """
    Définit les rôles possibles pour un utilisateur.
    """
    USER = "user"
    ADMIN = "admin"

class User(Base):
    """
    Représente un utilisateur de l'application.

    Attributes:
        id (int): L'identifiant unique de l'utilisateur.
        name (str): Le nom de l'utilisateur.
        email (str): L'adresse email de l'utilisateur (doit être unique).
        role (UserRole): Le rôle de l'utilisateur (par défaut 'user').
        created_at (datetime): La date et l'heure de création de l'utilisateur.
        updated_at (datetime): La date et l'heure de la dernière mise à jour de l'utilisateur.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    votes = relationship("Vote", back_populates="user")

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

class Activity(Base):
    """
    Représente une activité proposée par la municipalité.

    Attributes:
        id (int): L'identifiant unique de l'activité.
        title (str): Le titre de l'activité.
        description (str): Une description détaillée de l'activité.
        category (str): La catégorie de l'activité (ex: "sport", "culture").
        indoor_outdoor (IndoorOutdoor): Indique si l'activité est en intérieur, extérieur ou mixte.
        min_age (int): L'âge minimum recommandé pour l'activité.
        meta (JSON): Métadonnées supplémentaires au format JSON.
        min_temperature_celsius (float): Température minimale requise en Celsius.
        max_temperature_celsius (float): Température maximale requise en Celsius.
        max_wind_speed_kph (float): Vitesse maximale du vent en km/h.
        requires_clear_sky (bool): Indique si l'activité nécessite un ciel dégagé.
        min_air_quality_index (int): Indice de qualité de l'air minimal requis.
        max_air_quality_index (int): Indice de qualité de l'air maximal requis.
        average_rating (float): La note moyenne de l'activité.
        votes (int): Le nombre total de votes reçus pour l'activité.
        created_at (datetime): La date et l'heure de création de l'activité.
        updated_at (datetime): La date et l'heure de la dernière mise à jour de l'activité.
    """
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    indoor_outdoor = Column(Enum(IndoorOutdoor), default=IndoorOutdoor.MIX, nullable=False)
    min_age = Column(Integer, default=0)
    meta = Column(JSON, default={})
    min_temperature_celsius = Column(Float)
    max_temperature_celsius = Column(Float)
    max_wind_speed_kph = Column(Float)
    requires_clear_sky = Column(Boolean, default=False)
    min_air_quality_index = Column(Integer)
    max_air_quality_index = Column(Integer)
    average_rating = Column(Float, default=0.0)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instances = relationship("ActivityInstance", back_populates="activity")

class ActivityInstance(Base):
    """
    Représente une instance spécifique d'une activité, avec des détails temporels et géographiques.

    Attributes:
        id (int): L'identifiant unique de l'instance d'activité.
        activity_id (int): L'identifiant de l'activité associée.
        start_dt (datetime): La date et l'heure de début de l'instance.
        end_dt (datetime): La date et l'heure de fin de l'instance.
        location (str): Le lieu où se déroule l'instance de l'activité.
        activity (Activity): L'objet activité associé.
        created_at (datetime): La date et l'heure de création de l'instance.
        updated_at (datetime): La date et l'heure de la dernière mise à jour de l'instance.
    """
    __tablename__ = "activity_instances"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    start_dt = Column(DateTime, nullable=False)
    end_dt = Column(DateTime, nullable=False)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activity = relationship("Activity", back_populates="instances")

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
