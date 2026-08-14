from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    """Modèle pour tracer les activités récentes du système (module laboratoire)."""

    TYPE_CHOICES = [
        ('ECHANTILLON', 'Échantillon'),
        ('DEMANDE', 'Demande de devis'),
        ('FACTURE', 'Facture'),
        ('RECEPTION', 'Réception'),
        ('SORTIE', 'Sortie de stock'),
        ('CLIENT', 'Client'),
        ('ANALYSE', 'Analyse'),
        ('RAPPORT', 'Rapport'),
    ]

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Conserve le nom de table historique du module labo (app "core" avant
        # renommage en "laboratoire_core" pour eviter la collision avec le
        # "core" existant de ce projet) : preserve les donnees existantes.
        db_table = 'core_activity'
        ordering = ['-created_at']
        verbose_name = 'Activité'
        verbose_name_plural = 'Activités'

    def __str__(self):
        return f"{self.type} - {self.titre}"
