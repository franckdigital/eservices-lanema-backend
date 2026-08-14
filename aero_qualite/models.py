from django.conf import settings
from django.db import models

from aero_maintenance.models import OrdreTravail


class NonConformiteDAE(models.Model):
    GRAVITE_CHOICES = [
        ("MINEURE", "Mineure"),
        ("MAJEURE", "Majeure"),
        ("CRITIQUE", "Critique"),
    ]
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("EN_COURS", "En cours de traitement"),
        ("CLOTUREE", "Clôturée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="non_conformites"
    )
    gravite = models.CharField(max_length=10, choices=GRAVITE_CHOICES, default="MINEURE")
    description = models.TextField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="non_conformites_dae"
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="OUVERTE")
    date_creation = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class ActionCorrectiveDAE(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("EN_COURS", "En cours"),
        ("REALISEE", "Réalisée"),
    ]

    non_conformite = models.ForeignKey(NonConformiteDAE, on_delete=models.CASCADE, related_name="actions_correctives")
    description = models.TextField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_correctives_dae"
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="PLANIFIEE")
    date_prevue = models.DateField(null=True, blank=True)
    date_realisation = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_prevue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Action - {self.non_conformite.reference}"


class AuditQualiteDAE(models.Model):
    RESULTAT_CHOICES = [
        ("CONFORME", "Conforme"),
        ("NON_CONFORME", "Non conforme"),
        ("CONFORME_AVEC_RESERVES", "Conforme avec réserves"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_audit = models.CharField(max_length=100, blank=True)
    date_audit = models.DateField()
    resultat = models.CharField(max_length=25, choices=RESULTAT_CHOICES, default="CONFORME")

    class Meta:
        ordering = ["-date_audit"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
