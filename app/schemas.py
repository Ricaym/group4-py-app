
import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, constr, ConfigDict


class SexEnum(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class UserRole(str, enum.Enum):
    """
    Représente les rôles possibles pour un utilisateur dans l'application.
    """
    USER = "abonne"
    ADMIN = "administrateur"


class UtilisateurBase(BaseModel):
    """
    Schéma de base pour les informations d'un utilisateur,
    incluant le nom, l'email et le rôle.
    """
    nom: str = Field(validation_alias="name")
    email: EmailStr
    role: UserRole = UserRole.USER
    age: Optional[int] = Field(None, ge=0, description="L'âge de l'utilisateur")
    sex: Optional[SexEnum] = Field(None, description="Le sexe de l'utilisateur (M, F, O)")


class UtilisateurCreate(UtilisateurBase):
    """
    Schéma Pydantic pour la création d'un nouvel utilisateur.
    Inclut le mot de passe qui est haché avant d'être stocké.
    """
    mot_de_passe: constr(min_length=8, max_length=72)


class UtilisateurUpdate(UtilisateurBase):
    """
    Schéma Pydantic pour la mise à jour des informations d'un utilisateur existant.
    Tous les champs sont optionnels pour permettre des mises à jour partielles.
    """
    nom: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    age: Optional[int] = Field(None, ge=0, description="L'âge de l'utilisateur")
    sex: Optional[SexEnum] = Field(None, description="Le sexe de l'utilisateur (M, F, O)")
    mot_de_passe: Optional[constr(min_length=8, max_length=72)] = None


class UtilisateurRead(UtilisateurBase):
    """
    Schéma Pydantic pour la lecture des informations d'un utilisateur.
    Inclut des champs supplémentaires comme l'ID, l'état de vérification,
    et les horodatages de création et de mise à jour.
    """
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Nouveaux schémas pour la connexion
class UserLogin(BaseModel):
    """
    Schéma Pydantic pour les informations d'identification lors de la connexion.
    """
    email: EmailStr
    mot_de_passe: str

class Token(BaseModel):
    """
    Schéma Pydantic pour le jeton d'accès JWT retourné après une connexion réussie.
    """
    access_token: str
    token_type: str = "bearer"

class TokenWithUser(Token):
    """
    Schéma Pydantic pour le jeton d'accès et les informations de l'utilisateur
    retournés après une connexion réussie.
    """
    user: UtilisateurRead

class TokenData(BaseModel):
    """
    Schéma Pydantic pour les données contenues dans le jeton JWT.
    """
    email: Optional[str] = None

class PasswordUpdate(BaseModel):
    """
    Schéma Pydantic pour la mise à jour du mot de passe d'un utilisateur.
    Nécessite le mot de passe actuel et le nouveau mot de passe.
    """
    current_password: str
    new_password: str

# --- Schémas pour le Profil ---
class ProfileBase(BaseModel):
    """
    Schéma de base pour le profil d'un utilisateur.
    """
    outdoor_pref: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Préférence pour les activités de plein air (0=intérieur, 1=extérieur)")
    children_friendly: Optional[bool] = Field(False, description="Indique si l'utilisateur préfère les activités adaptées aux enfants")
    commute_time: Optional[int] = Field(None, ge=0, description="Temps de trajet maximal préféré en minutes")
    activity_intensity_pref: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Préférence pour l'intensité de l'activité (0=faible, 1=élevée)")

class ProfileCreate(ProfileBase):
    """
    Schéma pour la création d'un nouveau profil.
    """
    pass

class ProfileUpdate(ProfileBase):
    """
    Schéma pour la mise à jour d'un profil existant.
    Tous les champs sont optionnels pour permettre des mises à jour partielles.
    """
    outdoor_pref: Optional[float] = Field(None, ge=0.0, le=1.0)
    children_friendly: Optional[bool] = Field(None)
    commute_time: Optional[int] = Field(None, ge=0)
    activity_intensity_pref: Optional[float] = Field(None, ge=0.0, le=1.0)

class ProfileRead(ProfileBase):
    """
    Schéma pour la lecture d'un profil.
    Inclut l'ID du profil, l'ID de l'utilisateur associé et les horodatages.
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Schémas pour le Vote ---
class VoteBase(BaseModel):
    """
    Schéma de base pour un vote sur une activité.
    """
    ranking: list[int] = Field(..., description="Un classement des activités par ordre de préférence (liste d'IDs d'activités)")

class VoteCreate(VoteBase):
    """
    Schéma pour la création d'un nouveau vote.
    """
    pass

class VoteRead(VoteBase):
    """
    Schéma pour la lecture d'un vote.
    Inclut l'ID du vote, l'ID de l'utilisateur, l'ID de l'activité et l'horodatage.
    """
    id: int
    utilisateur_id: int = Field(alias="user_id") # Correspond à user_id dans le modèle SQLAlchemy
    created_at: datetime

    class Config:
        from_attributes = True

# --- Nouveaux schémas pour les Activités ---
class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    indoor_outdoor: str # Ou utiliser un Enum si défini ailleurs
    min_age: Optional[int] = Field(0, ge=0)
    min_temperature_celsius: Optional[float] = None
    max_temperature_celsius: Optional[float] = None
    max_wind_speed_kph: Optional[float] = None
    requires_clear_sky: Optional[bool] = False
    min_air_quality_index: Optional[int] = None
    max_air_quality_index: Optional[int] = None

class ActivityRead(ActivityBase):
    id: int
    average_rating: float
    votes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Nouveaux schémas pour les Recommandations ---
class RecommendationRequest(BaseModel):
    city: str = Field(..., description="La ville pour laquelle obtenir des recommandations")
    date: datetime = Field(..., description="La date pour laquelle obtenir des recommandations")

class RecommendationResponse(BaseModel):
    recommended_activities: List[ActivityRead]
    message: str = "Recommandations générées avec succès."
