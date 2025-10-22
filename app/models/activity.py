from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, Enum
from sqlalchemy.orm import relationship

from app.models._base import Base
from app.models.enums import IndoorOutdoor

class Activity(Base):
    """
    Représente une activité proposée par la municipalité.

    Attributes:
        id (int): L'identifiant unique de l'activité.
        title (str): Le titre de l'activité.
        description (str): Une description détaillée de l'activité.
        category (str): La catégorie de l'activité (ex: "sport", "culture"). :no-index:
        indoor_outdoor (IndoorOutdoor): Indique si l'activité est en intérieur, extérieur ou mixte.
        min_age (int): L'âge minimum recommandé pour l'activité.
        meta (JSON): Métadonnées supplémentaires au format JSON.
        min_temperature_celsius (float): Température minimale requise en Celsius.
        max_temperature_celsius (float): Température maximale requise en Celsius.
        max_wind_speed_kph (float): Vitesse maximale du vent en km/h.
        requires_clear_sky (bool): Indique si l'activité nécessite un ciel dégagé.
        min_air_quality_index (int): Indice de qualité de l'air minimal requis.
        max_air_quality_index (int): Indice de qualité de l'air maximal requis.
        average_rating (float): La note moyenne de l'activité. :no-index:
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
    historique_choix = relationship("Historique", back_populates="activite")
    recommandations = relationship("Recommandation", back_populates="activite")