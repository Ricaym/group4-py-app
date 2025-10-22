from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models._base import Base 
import datetime

class Historique(Base):
    """
    Conserve l'historique des recommandations et des choix d'un utilisateur.
    """
    __tablename__ = "historique"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activite_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    date_choix = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    utilisateur = relationship("User", back_populates="historique")
    activite = relationship("Activity", back_populates="historique_choix")

    def __repr__(self):
        return f"<Historique(id={self.id}, user_id={self.utilisateur_id}, activity_id={self.activite_id}, date_choix='{self.date_choix}')>"
