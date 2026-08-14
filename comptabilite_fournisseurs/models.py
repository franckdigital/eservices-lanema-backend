from django.db import models


class FournisseurComptable(models.Model):
    raison_sociale = models.CharField(max_length=255, unique=True)
    rccm = models.CharField(max_length=100, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    rib = models.CharField(max_length=100, blank=True, help_text="Coordonnées bancaires du fournisseur")
    contact_nom = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["raison_sociale"]

    def __str__(self) -> str:  # pragma: no cover
        return self.raison_sociale


class FactureFournisseur(models.Model):
    STATUT_CHOICES = [
        ("RECUE", "Reçue"),
        ("VALIDEE", "Validée"),
        ("PAYEE", "Payée"),
        ("LITIGE", "En litige"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    fournisseur = models.ForeignKey(FournisseurComptable, on_delete=models.CASCADE, related_name="factures")
    objet = models.CharField(max_length=255, blank=True)
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_reception = models.DateField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="RECUE")
    piece_jointe = models.FileField(upload_to="comptabilite/factures_fournisseurs/", null=True, blank=True)

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class PaiementFournisseur(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ("VIREMENT", "Virement"),
        ("CHEQUE", "Chèque"),
        ("ESPECES", "Espèces"),
    ]

    facture_fournisseur = models.ForeignKey(
        FactureFournisseur, on_delete=models.CASCADE, related_name="paiements"
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_paiement = models.DateField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=15, choices=MODE_PAIEMENT_CHOICES, default="VIREMENT")
    reference_paiement = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-date_paiement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Paiement {self.facture_fournisseur.reference} - {self.date_paiement}"
