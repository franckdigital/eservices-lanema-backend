"""
Chiffrement symétrique (Fernet) du mot de passe des comptes email DFIR — au
repos en base, plus jamais stocké en clair. La clé est dérivée de
settings.SECRET_KEY (aucune variable d'environnement supplémentaire à gérer :
la sécurité repose sur le même secret racine que le reste de l'application,
déjà celui qui protège sessions et jetons de réinitialisation de mot de
passe).
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_value(raw: str) -> str:
    if not raw:
        return ""
    return _fernet().encrypt(raw.encode()).decode()


def decrypt_value(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        # Ancienne valeur en clair (comptes créés avant l'ajout du
        # chiffrement) : on la retourne telle quelle plutôt que d'échouer.
        return token
