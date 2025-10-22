from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models._base import Base 

class Recommandation(Base):
    """
    Lie les activités aux conditions météo et aux préférences utilisateur,
    représentant une recommandation personnalisée.
    """
    __tablename__ = "recommandations"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meteo_id = Column(Integer, ForeignKey("meteo.id"), nullable=False)
    activite_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    score = Column(Float, nullable=False) # pertinence de la recommandation

    utilisateur = relationship("User", back_populates="recommandations")
    meteo = relationship("Meteo", back_populates="recommendations")
    activite = relationship("Activity", back_populates="recommandations")

    def __repr__(self):
        return f"<Recommandation(id={self.id}, user_id={self.utilisateur_id}, activity_id={self.activite_id}, score={self.score})>"
