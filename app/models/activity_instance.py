from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models._base import Base

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