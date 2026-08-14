from django.db import models

from dfir_assistance.models import MissionAssistance
from dfir_formations.models import SessionFormation
from dfir_participants.models import EntrepriseDFIR
from dfir_recherche.models import ProjetRecherche


class FactureDFIR(models.Model):
    TYPE_CHOICES = [
        ("FORMATION", "Formation"),
        ("ASSISTANCE", "Assistance technique"),
        ("RECHERCHE", "Recherche"),
    ]
    STATUT_CHOICES = [
        ("EMISE", "Émise"),
        ("PAYEE", "Payée"),
        ("IMPAYEE", "Impayée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_prestation = models.CharField(max_length=15, choices=TYPE_CHOICES, default="FORMATION")
    session = models.ForeignKey(
        SessionFormation, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    mission = models.ForeignKey(
        MissionAssistance, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    projet_recherche = models.ForeignKey(
        ProjetRecherche, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    entreprise = models.ForeignKey(EntrepriseDFIR, on_delete=models.CASCADE, related_name="factures_dfir")
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="EMISE")
    date_emission = models.DateField(auto_now_add=True)
    date_paiement = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
