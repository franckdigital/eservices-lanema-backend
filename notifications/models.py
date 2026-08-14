import logging

import requests
from django.contrib.auth.models import User
from django.db import models

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class Notification(models.Model):
    TYPE_CHOICES = [
        ("INFO", "Information"),
        ("ALERTE", "Alerte"),
        ("STOCK", "Stock"),
        ("DEMANDE", "Demande"),
        ("QUALITE", "Qualité"),
        ("FACTURATION", "Facturation"),
        ("METROLOGIE", "Métrologie"),
        ("ECHANTILLON", "Échantillon"),
        ("ESSAI", "Essai"),
    ]

    PRIORITE_CHOICES = [
        ("BASSE", "Basse"),
        ("NORMALE", "Normale"),
        ("HAUTE", "Haute"),
        ("URGENTE", "Urgente"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="labo_notifications",
    )
    titre = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INFO")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default="NORMALE")
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    lien = models.CharField(max_length=255, blank=True, help_text="Lien vers la ressource concernée")

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


def _envoyer_push(tokens_titres_messages):
    """Send one or more push messages via the Expo push API.

    tokens_titres_messages: iterable of (expo_push_token, titre, message) tuples.
    """
    messages = [
        {"to": token, "title": titre, "body": message, "sound": "default"}
        for token, titre, message in tokens_titres_messages
        if token
    ]
    if not messages:
        return
    try:
        requests.post(EXPO_PUSH_URL, json=messages, timeout=5)
    except requests.RequestException:
        logger.warning("Échec de l'envoi de la notification push Expo", exc_info=True)


def _expo_push_token(user):
    """Lit expo_push_token sur le ClientProfile du labo lie a cet utilisateur, s'il existe."""
    profile = getattr(user, "client_profile", None)
    return getattr(profile, "expo_push_token", None)


def creer_notification(user, titre, message="", type_notification="INFO", priorite="NORMALE", lien=""):
    """Helper function to create a notification for a user"""
    notification = Notification.objects.create(
        user=user,
        titre=titre,
        message=message,
        type_notification=type_notification,
        priorite=priorite,
        lien=lien
    )
    _envoyer_push([(_expo_push_token(user), titre, message)])
    return notification


def notifier_utilisateurs_par_role(role, titre, message="", type_notification="INFO", priorite="NORMALE", lien=""):
    """Create notifications for all users with a specific role (role du ClientProfile labo)"""
    users = list(User.objects.filter(client_profile__role=role, is_active=True))
    notifications = [
        Notification(
            user=user,
            titre=titre,
            message=message,
            type_notification=type_notification,
            priorite=priorite,
            lien=lien
        )
        for user in users
    ]
    Notification.objects.bulk_create(notifications)
    _envoyer_push([(_expo_push_token(user), titre, message) for user in users])
    return len(notifications)


def notifier_admins(titre, message="", type_notification="ALERTE", priorite="HAUTE", lien=""):
    """Create notifications for all admin users (role du ClientProfile labo)"""
    admins = list(User.objects.filter(client_profile__role__in=["ADMIN", "SUPERADMIN"], is_active=True))
    notifications = [
        Notification(
            user=admin,
            titre=titre,
            message=message,
            type_notification=type_notification,
            priorite=priorite,
            lien=lien
        )
        for admin in admins
    ]
    Notification.objects.bulk_create(notifications)
    _envoyer_push([(_expo_push_token(admin), titre, message) for admin in admins])
    return len(notifications)
