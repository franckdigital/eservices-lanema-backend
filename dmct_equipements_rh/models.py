from django.conf import settings
from django.db import models


class EquipementReference(models.Model):
    STATUT_CHOICES = [
        ("OPERATIONNEL", "Opérationnel"),
        ("MAINTENANCE", "Maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    code = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    est_etalon = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OPERATIONNEL")
    date_dernier_etalonnage = models.DateField(null=True, blank=True)
    date_prochain_etalonnage = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["designation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class PanneEquipementReference(models.Model):
    equipement = models.ForeignKey(EquipementReference, on_delete=models.CASCADE, related_name="pannes")
    date_panne = models.DateField(auto_now_add=True)
    date_reparation = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_panne"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Panne {self.equipement.code} - {self.date_panne}"


class MaintenancePreventiveReference(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("REALISEE", "Réalisée"),
        ("REPORTEE", "Reportée"),
    ]

    equipement = models.ForeignKey(EquipementReference, on_delete=models.CASCADE, related_name="maintenances_preventives")
    date_prevue = models.DateField()
    date_realisee = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")

    class Meta:
        ordering = ["-date_prevue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Maintenance {self.equipement.code} - {self.date_prevue}"


class EtalonnageReference(models.Model):
    equipement = models.ForeignKey(EquipementReference, on_delete=models.CASCADE, related_name="etalonnages")
    date_etalonnage = models.DateField()
    date_prochain = models.DateField()
    resultat = models.CharField(max_length=50, default="CONFORME")

    class Meta:
        ordering = ["-date_etalonnage"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Etalonnage {self.equipement.code} - {self.date_etalonnage}"


class CertificationAgentDMCT(models.Model):
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certifications_dmct"
    )
    competence = models.CharField(max_length=255)
    date_obtention = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_obtention"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.agent} - {self.competence}"

    @property
    def valide(self) -> bool:
        from django.utils import timezone
        return self.date_expiration is None or self.date_expiration >= timezone.now().date()


class FormationDMCT(models.Model):
    titre = models.CharField(max_length=255)
    date_formation = models.DateField()
    nombre_participants = models.PositiveIntegerField(default=0)
    duree_heures = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    class Meta:
        ordering = ["-date_formation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre
