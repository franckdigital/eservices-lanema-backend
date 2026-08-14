from django.db import models

from aero_clients.models import ClientAeronautique
from aero_maintenance.models import OrdreTravail


class FactureDAE(models.Model):
    STATUT_CHOICES = [
        ("EMISE", "Émise"),
        ("PAYEE", "Payée"),
        ("IMPAYEE", "Impayée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="factures")
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="EMISE")
    date_emission = models.DateField(auto_now_add=True)
    date_paiement = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
