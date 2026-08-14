from django.db import models

from dmct_clients.models import ClientDMCT
from dmct_prestations.models import PrestationDMCT


class FactureDMCT(models.Model):
    STATUT_CHOICES = [
        ("EMISE", "Émise"),
        ("PAYEE", "Payée"),
        ("IMPAYEE", "Impayée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    prestation = models.ForeignKey(
        PrestationDMCT, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    client = models.ForeignKey(ClientDMCT, on_delete=models.CASCADE, related_name="factures")
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="EMISE")
    date_emission = models.DateField(auto_now_add=True)
    date_paiement = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
