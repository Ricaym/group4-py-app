
import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, constr, ConfigDict


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
