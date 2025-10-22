import enum

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
    USER = "abonne"
    ADMIN = "administrateur"