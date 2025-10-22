from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import relationship
from app.models._base import Base 

class Meteo(Base):
    """
    Représente les informations météorologiques utilisées pour recommander des activités.
    """
    __tablename__ = "meteo"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    condition = Column(String, nullable=False) # ex: "ensoleillé", "pluvieux", "nuageux"
    ville = Column(String, nullable=False)
    date = Column(Date, nullable=False)

    recommendations = relationship("Recommandation", back_populates="meteo")

    def __repr__(self):
        return f"<Meteo(id={self.id}, ville='{self.ville}', date='{self.date}', temp={self.temperature})>"
