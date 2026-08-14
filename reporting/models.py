from django.contrib.auth.models import User
from django.db import models


class Rapport(models.Model):
    TYPE_CHOICES = [
        ("SYNTHSE_DEMANDES", "Synthèse demandes"),
        ("SYNTHSE_FACTURATION", "Synthèse facturation"),
        ("PERSONNALISE", "Personnalisé"),
    ]

    type_rapport = models.CharField(max_length=50, choices=TYPE_CHOICES, default="PERSONNALISE")
    titre = models.CharField(max_length=255)
    parametres = models.JSONField(default=dict, blank=True)
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rapports",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class RapportEssai(models.Model):
    """Rapport d'essai avec workflow de validation/signature electronique,
    distinct du Rapport generique ci-dessus (admin/synthese)."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("EN_ATTENTE_VALIDATION", "En attente de validation"),
        ("VALIDE", "Validé"),
        ("CORRIGE", "Corrigé"),
        ("SIGNE", "Signé"),
    ]

    essai = models.ForeignKey(
        "qualite.Essai", on_delete=models.CASCADE, related_name="rapports_essai"
    )
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default="BROUILLON")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_soumission = models.DateField(null=True, blank=True)
    date_validation = models.DateField(null=True, blank=True)
    valide_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="rapports_essai_valides"
    )
    signe_electroniquement = models.BooleanField(default=False)
    date_signature = models.DateField(null=True, blank=True)
    delai_reglementaire_jours = models.PositiveIntegerField(
        null=True, blank=True, help_text="Delai reglementaire de remise, en jours, a compter de la fin de l'essai"
    )

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Rapport {self.essai.numero} ({self.statut})"
