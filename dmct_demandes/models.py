from django.db import models

from dmct_clients.models import ClientDMCT


class DemandeDMCT(models.Model):
    TYPE_CHOICES = [
        ("VERIFICATION", "Vérification"),
        ("ETALONNAGE", "Étalonnage"),
    ]
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("ENREGISTREE", "Enregistrée"),
        ("EN_COURS", "En cours"),
        ("TERMINEE", "Terminée"),
        ("ANNULEE", "Annulée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_demande = models.CharField(max_length=20, choices=TYPE_CHOICES, default="VERIFICATION")
    client = models.ForeignKey(ClientDMCT, on_delete=models.CASCADE, related_name="demandes")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_enregistrement = models.DateTimeField(null=True, blank=True)
    date_prise_charge = models.DateTimeField(null=True, blank=True)
    date_limite_prise_charge = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
