from django.conf import settings
from django.db import models


class PieceComptable(models.Model):
    TYPE_CHOICES = [
        ("FACTURE_CLIENT", "Facture client"),
        ("FACTURE_FOURNISSEUR", "Facture fournisseur"),
        ("RECU", "Reçu"),
        ("BON_COMMANDE", "Bon de commande"),
        ("AUTRE", "Autre"),
    ]
    STATUT_CHOICES = [
        ("ENREGISTREE", "Enregistrée"),
        ("VALIDEE", "Validée"),
        ("REJETEE", "Rejetée"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    type_piece = models.CharField(max_length=25, choices=TYPE_CHOICES, default="AUTRE")
    source_reference = models.CharField(
        max_length=100, blank=True,
        help_text="Numero du document d'origine (ex: numero de facture)",
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_piece = models.DateField(auto_now_add=True)
    fichier = models.FileField(upload_to="comptabilite/pieces/", null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default="ENREGISTREE")
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="pieces_validees"
    )
    date_validation = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_piece"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
