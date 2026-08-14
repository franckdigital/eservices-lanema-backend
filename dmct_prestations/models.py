from django.conf import settings
from django.db import models

from dmct_demandes.models import DemandeDMCT
from dmct_instruments.models import InstrumentMesure


class PrestationDMCT(models.Model):
    TYPE_CHOICES = [
        ("CONTROLE", "Contrôle"),
        ("ETALONNAGE", "Étalonnage"),
        ("VERIFICATION", "Vérification"),
        ("CERTIFICATION", "Certification"),
    ]
    LIEU_CHOICES = [
        ("SUR_SITE", "Sur site"),
        ("LABORATOIRE", "Laboratoire"),
    ]
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("TERMINEE", "Terminée"),
        ("ANNULEE", "Annulée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    demande = models.ForeignKey(
        DemandeDMCT, on_delete=models.SET_NULL, null=True, blank=True, related_name="prestations"
    )
    instrument = models.ForeignKey(
        InstrumentMesure, on_delete=models.SET_NULL, null=True, blank=True, related_name="prestations"
    )
    type_prestation = models.CharField(max_length=20, choices=TYPE_CHOICES, default="CONTROLE")
    lieu = models.CharField(max_length=20, choices=LIEU_CHOICES, default="LABORATOIRE")
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="prestations_dmct"
    )
    conforme = models.BooleanField(null=True, blank=True)
    urgent = models.BooleanField(default=False)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    date_fin_prevue = models.DateTimeField(null=True, blank=True)
    date_livraison_certificat = models.DateField(null=True, blank=True)
    cout_revient = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
