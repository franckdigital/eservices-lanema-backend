from django.conf import settings
from django.db import models

from aero_clients.models import Aeronef
from aero_stock.models import PieceRechange


class OrdreTravail(models.Model):
    TYPE_CHOICES = [
        ("PREVENTIVE", "Maintenance préventive"),
        ("CORRECTIVE", "Maintenance corrective"),
        ("URGENCE", "Urgence"),
    ]
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("ANNULE", "Annulé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    aeronef = models.ForeignKey(Aeronef, on_delete=models.CASCADE, related_name="ordres_travail")
    type_intervention = models.CharField(max_length=20, choices=TYPE_CHOICES, default="CORRECTIVE")
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordres_travail_dae"
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_prise_charge = models.DateTimeField(null=True, blank=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    piece_utilisee = models.ForeignKey(
        PieceRechange, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordres_travail"
    )

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class RoueAeronef(models.Model):
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_INSPECTION", "En inspection"),
        ("REPAREE", "Réparée"),
        ("REMPLACEE", "Remplacée"),
        ("NON_CONFORME", "Non conforme"),
    ]

    numero_serie = models.CharField(max_length=50, unique=True)
    aeronef = models.ForeignKey(Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="roues")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    nombre_cycles = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["numero_serie"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_serie


class InspectionRoue(models.Model):
    TYPE_CHOICES = [
        ("INSPECTION_PERIODIQUE", "Inspection périodique"),
        ("REPARATION", "Réparation"),
        ("REMPLACEMENT", "Remplacement"),
    ]

    roue = models.ForeignKey(RoueAeronef, on_delete=models.CASCADE, related_name="inspections")
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections_roues"
    )
    date_inspection = models.DateField(auto_now_add=True)
    conforme = models.BooleanField(default=True)
    type_inspection = models.CharField(max_length=25, choices=TYPE_CHOICES, default="INSPECTION_PERIODIQUE")

    class Meta:
        ordering = ["-date_inspection"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.roue.numero_serie} - {self.date_inspection}"


class BatterieAeronef(models.Model):
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_TEST", "En test"),
        ("RECHARGEE", "Rechargée"),
        ("REPAREE", "Réparée"),
        ("REMPLACEE", "Remplacée"),
        ("HORS_SERVICE", "Hors service"),
    ]

    numero_serie = models.CharField(max_length=50, unique=True)
    aeronef = models.ForeignKey(Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="batteries")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    date_mise_en_service = models.DateField(null=True, blank=True)
    date_derniere_maintenance = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["numero_serie"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_serie
