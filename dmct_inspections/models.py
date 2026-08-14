from django.db import models

from dmct_clients.models import ClientDMCT


class InspectionDMCT(models.Model):
    CATEGORIE_CHOICES = [
        ("INSPECTION", "Inspection"),
        ("CONTROLE_TECHNIQUE", "Contrôle technique"),
    ]
    TYPE_CONTROLE_CHOICES = [
        ("PROGRAMME", "Programmé"),
        ("INOPINE", "Inopiné"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    etablissement = models.ForeignKey(
        ClientDMCT, on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections"
    )
    categorie = models.CharField(max_length=25, choices=CATEGORIE_CHOICES, default="INSPECTION")
    type_controle = models.CharField(max_length=15, choices=TYPE_CONTROLE_CHOICES, default="PROGRAMME")
    date_inspection = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)
    conforme = models.BooleanField(null=True, blank=True)
    sanction_emise = models.BooleanField(default=False)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_inspection"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class ContreVisiteDMCT(models.Model):
    RESULTAT_CHOICES = [
        ("CONFORME", "Conforme"),
        ("NON_CONFORME", "Non conforme"),
    ]

    inspection = models.ForeignKey(InspectionDMCT, on_delete=models.CASCADE, related_name="contre_visites")
    date_contre_visite = models.DateField()
    resultat = models.CharField(max_length=15, choices=RESULTAT_CHOICES, default="CONFORME")

    class Meta:
        ordering = ["-date_contre_visite"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Contre-visite {self.inspection.reference} - {self.date_contre_visite}"
