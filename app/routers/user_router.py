
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models._base import Base
from app.models.user import User
from app.models.profile import Profile 
from app import schemas
from passlib.context import CryptContext
import uuid 
import smtplib
from email.mime.text import MIMEText
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta

from app.core.config import settings

# Imports Brevo # REMOVED: No longer using Brevo for email sending
# import sib_api_v3_sdk
# from sib_api_v3_sdk.rest import ApiException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration JWT (peut être déplacée vers app/core/config.py pour une meilleure organisation)
# Pour cet exemple, nous allons les définir ici.
# SECRET_KEY = "votre_clé_secrète_super_sécurisée" # REMPLACER PAR UNE VRAIE CLÉ SECRÈTE
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

def get_password_hash(password: str) -> str:
    """
    Hache un mot de passe en texte clair en utilisant bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe en texte clair correspond à un mot de passe haché.
    """
    return pwd_context.verify(plain_password, hashed_password)

# Fonction pour envoyer un email de vérification réel
def send_verification_email(user_name: str, user_email: str, verification_token: str): # Ajout de user_email ici
    """
    Envoie un email de vérification à l'utilisateur avec un lien d'activation via Zoho Mail.
    """
    verification_link = f"http://localhost:8000/users/verify-email?token={verification_token}"
    
    html_body = f'''
    <html>
        <body>
            <p>Bonjour {user_name},</p>
            <p>Veuillez cliquer sur le bouton ci-dessous pour activer votre compte :</p>
            <p>
                <a href="{verification_link}" style="background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 8px;">Activer mon compte</a>
            </p>
            <p>Cordialement,</p>
            <p>L'équipe Météo Activités</p>
        </body>
    </html>
    '''
    
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = "Activez votre compte Météo Activités"
    msg['From'] = settings.smtp_user
    msg['To'] = user_email

    # --- DEBUG: Affichage des valeurs des variables avant l'envoi ---
    print(f"DEBUG: (user_router) Hôte SMTP : {settings.smtp_host}")
    print(f"DEBUG: (user_router) Port SMTP : {settings.smtp_port}")
    print(f"DEBUG: (user_router) Utilisateur SMTP : {settings.smtp_user}")
    print(f"DEBUG: (user_router) Mot de passe SMTP (partiel) : {settings.smtp_pass}") 
    print(f"DEBUG: (user_router) Nom de l'utilisateur : {user_name}")
    print(f"DEBUG: (user_router) Email de l'utilisateur : {user_email}")
    print(f"DEBUG: (user_router) Token de vérification : {verification_token}")
    print(f"DEBUG: (user_router) Lien de vérification : {verification_link}")
    print(f"DEBUG: (user_router) Sujet de l'email : {msg['Subject']}")
    print(f"DEBUG: (user_router) Expéditeur de l'email : {msg['From']}")
    print(f"DEBUG: (user_router) Destinataire de l'email : {msg['To']}")
    print("-" * 30)

    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.smtp_user, user_email, msg.as_string())
        print(f"Email de vérification envoyé à {user_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email via Zoho Mail: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de l'envoi de l'email de vérification.")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crée un jeton d'accès JWT pour l'authentification de l'utilisateur.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes) # Utiliser settings.access_token_expire_minutes
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm) # Utiliser settings.secret_key et settings.algorithm
    return encoded_jwt

@router.post("/", response_model=schemas.UtilisateurRead, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    """
    Crée un nouvel utilisateur.
    """
    if user.role == schemas.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La création de comptes administrateur via l'API n'est pas autorisée.")

    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà enregistré")

    hashed_password = get_password_hash(user.mot_de_passe)
    verification_token = str(uuid.uuid4()) # Génère un token unique

    db_user = User(
        name=user.nom,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        is_verified=False, # Nouveau compte non vérifié par défaut
        verification_token=verification_token,
        age=user.age,
        sex=user.sex
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    send_verification_email(db_user.name, db_user.email, verification_token) # Passer db_user.name et db_user.email

    return schemas.UtilisateurRead.model_validate(db_user)

@router.post("/token", response_model=schemas.TokenWithUser) # Changement ici: Utilisé TokenWithUser
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne un jeton d'accès JWT.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides username",
            headers={"WWW-Authenticate": "Bearer"},
        )

    is_password_valid = verify_password(form_data.password, user.hashed_password)
    print(f"Résultat de verify_password : {is_password_valid}")
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Votre compte n'a pas été vérifié. Veuillez vérifier votre email.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes) # Utiliser settings.access_token_expire_minutes
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UtilisateurRead.model_validate(user) # Ajout des infos utilisateur ici
    }

# Fonction utilitaire pour obtenir l'utilisateur actuel (nécessaire pour les routes protégées)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User: # <-- Ajout du type de retour pour la dépendance
    """
    Dépendance pour récupérer l'utilisateur actuellement authentifié à partir du jeton JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]) # Utiliser settings.secret_key et settings.algorithm
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first() # <-- Modifié ici: models.User -> User
    if user is None:
        raise credentials_exception
    return user

# Exemple de route protégée (vous pouvez l'ajouter pour tester)
@router.get("/me/", response_model=schemas.UtilisateurRead)
async def read_users_me(current_user: User = Depends(get_current_user)): # <-- Modifié ici: models.User -> User
    """
    Récupère les informations de l'utilisateur actuellement authentifié.
    """
    return current_user

@router.get("/verify-email", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Vérifie l'adresse email d'un utilisateur à l'aide d'un jeton de vérification.
    """
    user = db.query(User).filter(User.verification_token == token).first() # <-- Modifié ici: models.User -> User

    # Base HTML et CSS pour un look moderne
    base_html_template = """
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #e9ecef; /* Fond gris clair */
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .card {{
                background-color: #ffffff;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 500px;
                width: 90%;
                animation: fadeIn 0.8s ease-out;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(-20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            h1 {{
                font-size: 2.2em;
                margin-bottom: 20px;
            }}
            p {{
                font-size: 1.1em;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .icon {{
                font-size: 4em;
                margin-bottom: 20px;
            }}
            /* Couleurs spécifiques aux états */
            .success h1, .success .icon {{ color: #28a745; /* Vert pour le succès */ }}
            .warning h1, .warning .icon {{ color: #ffc107; /* Jaune pour l'avertissement */ }}
            .error h1, .error .icon {{ color: #dc3545; /* Rouge pour l'erreur */ }}
            .button {{
                display: inline-block;
                background-color: #007bff; /* Bleu standard */
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }}
            .button:hover {{
                background-color: #0056b3;
            }}
        </style>
    </head>
    <body>
        <div class="card {status_class}">
            <i class="icon {icon_class}"></i>
            <h1>{heading}</h1>
            <p>{message}</p>
            {extra_content}
        </div>
    </body>
    </html>
    """

    if not user:
        return HTMLResponse(content=base_html_template.format(
            title="Erreur de vérification",
            status_class="error",
            icon_class="fas fa-times-circle",
            heading="Erreur de vérification",
            message="Le token de vérification est invalide ou a expiré. Veuillez réessayer ou contacter le support.",
            extra_content=""
        ), status_code=status.HTTP_400_BAD_REQUEST)

    if user.is_verified:
        return HTMLResponse(content=base_html_template.format(
            title="Compte déjà vérifié",
            status_class="warning",
            icon_class="fas fa-exclamation-triangle",
            heading="Compte déjà vérifié",
            message="Votre compte est déjà vérifié. Vous pouvez maintenant vous connecter.",
            #extra_content='<a href="http://localhost:8000/docs" class="button">Se connecter</a>'
            extra_content=""
        ), status_code=status.HTTP_400_BAD_REQUEST)

    user.is_verified = True
    user.verification_token = None # Le token n'est plus nécessaire après vérification
    db.commit()
    db.refresh(user)

    return HTMLResponse(content=base_html_template.format(
        title="Vérification réussie !",
        status_class="success",
        icon_class="fas fa-check-circle",
        heading="Vérification réussie !",
        message="Votre compte a été vérifié avec succès ! Vous pouvez maintenant vous connecter.",
       # extra_content='<a href="http://localhost:8000/docs" class="button">Se connecter</a>'
        extra_content=""
    ))

@router.put("/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_update: schemas.PasswordUpdate,
    current_user: User = Depends(get_current_user), # <-- Modifié ici: models.User -> User
    db: Session = Depends(get_db)
):
    """
    Met à jour le mot de passe de l'utilisateur actuellement authentifié.
    Nécessite le mot de passe actuel pour des raisons de sécurité.
    """
    # Vérifier si l'ancien mot de passe est correct
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ancien mot de passe incorrect",
        )
    
    # Hasher le nouveau mot de passe
    hashed_new_password = get_password_hash(password_update.new_password)
    
    # Mettre à jour le mot de passe de l'utilisateur
    current_user.hashed_password = hashed_new_password
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Mot de passe mis à jour avec succès"}

# --- Endpoints de gestion des profils ---

@router.post("/me/profile", response_model=schemas.ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_my_profile(
    profile_data: schemas.ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau profil pour l'utilisateur actuellement authentifié.
    Un utilisateur ne peut avoir qu'un seul profil.
    """
    db_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if db_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le profil existe déjà pour cet utilisateur.")

    new_profile = Profile(**profile_data.model_dump(), user_id=current_user.id)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

@router.get("/me/profile", response_model=schemas.ProfileRead)
async def read_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le profil de l'utilisateur actuellement authentifié.
    """
    db_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if db_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé pour cet utilisateur.")
    return db_profile

@router.put("/me/profile", response_model=schemas.ProfileRead)
async def update_my_profile(
    profile_data: schemas.ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le profil de l'utilisateur actuellement authentifié.
    """
    db_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if db_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé pour cet utilisateur.")

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/", response_model=List[schemas.UtilisateurRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Récupère une liste d'utilisateurs.
    """
    users = db.query(User).offset(skip).limit(limit).all() # <-- Modifié ici: models.User -> User
    return [schemas.UtilisateurRead.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=schemas.UtilisateurRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Récupère un utilisateur spécifique par son ID.
    """
    user = db.query(User).filter(User.id == user_id).first() # <-- Modifié ici: models.User -> User
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    return schemas.UtilisateurRead.model_validate(user)

@router.put("/{user_id}", response_model=schemas.UtilisateurRead)
def update_user(user_id: int, user_update: schemas.UtilisateurUpdate, db: Session = Depends(get_db)):
    """
    Met à jour les informations d'un utilisateur existant.
    """
    db_user = db.query(User).filter(User.id == user_id).first() # <-- Modifié ici: models.User -> User
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    update_data = user_update.model_dump(exclude_unset=True)
    if "role" in update_data and update_data["role"] == schemas.UserRole.ADMIN and db_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La promotion au rôle d'administrateur n'est pas autorisée via cette API.")

    if "mot_de_passe" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data["mot_de_passe"])
        del update_data["mot_de_passe"]

    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return schemas.UtilisateurRead.model_validate(db_user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Supprime un utilisateur spécifique par son ID.
    """
    db_user = db.query(User).filter(User.id == user_id).first() # <-- Modifié ici: models.User -> User
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    db.delete(db_user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}
