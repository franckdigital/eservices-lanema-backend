from django.db import models

from comptabilite_pieces.models import PieceComptable


class CompteComptable(models.Model):
    TYPE_CHOICES = [
        ("ACTIF", "Actif"),
        ("PASSIF", "Passif"),
        ("CHARGE", "Charge"),
        ("PRODUIT", "Produit"),
    ]

    numero = models.CharField(max_length=20, unique=True, help_text="Ex: 512000")
    intitule = models.CharField(max_length=255)
    type_compte = models.CharField(max_length=10, choices=TYPE_CHOICES, default="ACTIF")

    class Meta:
        ordering = ["numero"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.numero} - {self.intitule}"


class JournalComptable(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="Ex: BQ, CA, VE, AC, OD")
    libelle = models.CharField(max_length=255)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} - {self.libelle}"


class EcritureComptable(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    journal = models.ForeignKey(JournalComptable, on_delete=models.CASCADE, related_name="ecritures")
    date_ecriture = models.DateField(auto_now_add=True)
    compte_debit = models.ForeignKey(
        CompteComptable, on_delete=models.CASCADE, related_name="ecritures_debit"
    )
    compte_credit = models.ForeignKey(
        CompteComptable, on_delete=models.CASCADE, related_name="ecritures_credit"
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    libelle = models.CharField(max_length=255, blank=True)
    piece = models.ForeignKey(
        PieceComptable, on_delete=models.SET_NULL, null=True, blank=True, related_name="ecritures"
    )
    valide = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_ecriture"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
