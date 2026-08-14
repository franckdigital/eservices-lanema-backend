from django.contrib.auth.models import User
from django.db import models


class Equipement(models.Model):
    STATUT_CHOICES = [
        ("OPERATIONNEL", "Opérationnel"),
        ("ETALONNAGE_REQUIS", "Étalonnage requis"),
        ("MAINTENANCE", "Maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    TYPE_CHOICES = [
        ("BALANCE", "Balance"),
        ("ETUVE", "Étuve"),
        ("PRESSE", "Presse"),
        ("THERMOMETRE", "Thermomètre"),
        ("AUTRE", "Autre"),
    ]

    code = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="BALANCE")
    marque = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    date_dernier_etalonnage = models.DateField(null=True, blank=True)
    date_prochain_etalonnage = models.DateField(null=True, blank=True)
    localisation = models.CharField(max_length=255, blank=True)
    laboratoire = models.ForeignKey(
        "laboratoires.Laboratoire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipements",
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipements_metrologie",
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OPERATIONNEL")

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class Etalonnage(models.Model):
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="etalonnages")
    date_etalonnage = models.DateField()
    date_prochain = models.DateField()
    prestataire = models.CharField(max_length=255, blank=True)
    resultat = models.CharField(max_length=50, default="CONFORME")

    def __str__(self) -> str:  # pragma: no cover
        return f"Etalonnage {self.equipement.code} - {self.date_etalonnage}"


class PanneEquipement(models.Model):
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="pannes")
    date_panne = models.DateField(auto_now_add=True)
    date_reparation = models.DateField(null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_panne"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Panne {self.equipement.code} - {self.date_panne}"


class MaintenancePreventive(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("REALISEE", "Réalisée"),
        ("REPORTEE", "Reportée"),
    ]

    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="maintenances_preventives")
    date_prevue = models.DateField()
    date_realisee = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    reussie = models.BooleanField(null=True, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_prevue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Maintenance {self.equipement.code} - {self.date_prevue}"
