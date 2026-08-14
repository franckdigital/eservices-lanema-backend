from django.conf import settings
from django.db import models


class EquipementAtelier(models.Model):
    STATUT_CHOICES = [
        ("OPERATIONNEL", "Opérationnel"),
        ("MAINTENANCE", "Maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    code = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OPERATIONNEL")

    class Meta:
        ordering = ["designation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class PanneEquipementAtelier(models.Model):
    equipement = models.ForeignKey(EquipementAtelier, on_delete=models.CASCADE, related_name="pannes")
    date_panne = models.DateField(auto_now_add=True)
    date_reparation = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_panne"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Panne {self.equipement.code} - {self.date_panne}"


class MaintenancePreventiveAtelier(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("REALISEE", "Réalisée"),
        ("REPORTEE", "Reportée"),
    ]

    equipement = models.ForeignKey(EquipementAtelier, on_delete=models.CASCADE, related_name="maintenances_preventives")
    date_prevue = models.DateField()
    date_realisee = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")

    class Meta:
        ordering = ["-date_prevue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Maintenance {self.equipement.code} - {self.date_prevue}"


class EtalonnageAtelier(models.Model):
    equipement = models.ForeignKey(EquipementAtelier, on_delete=models.CASCADE, related_name="etalonnages")
    date_etalonnage = models.DateField()
    date_prochain = models.DateField()
    resultat = models.CharField(max_length=50, default="CONFORME")

    class Meta:
        ordering = ["-date_etalonnage"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Etalonnage {self.equipement.code} - {self.date_etalonnage}"


class CertificationTechnicien(models.Model):
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certifications_dae"
    )
    competence = models.CharField(max_length=255)
    date_obtention = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_obtention"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.technicien} - {self.competence}"

    @property
    def valide(self) -> bool:
        from django.utils import timezone
        return self.date_expiration is None or self.date_expiration >= timezone.now().date()
