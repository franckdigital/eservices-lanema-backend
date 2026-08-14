from django.contrib.auth.models import User
from django.db import models


class ValidationResponsableMixin(models.Model):
    """Champs communs de validation par le responsable labo (signature + cachet
    appliques a partir de son ClientProfile), partages par Proforma, BonCommande
    et Facture."""

    valide_par_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    date_validation_responsable = models.DateField(null=True, blank=True)
    signature_responsable_appliquee = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Proforma(ValidationResponsableMixin):
    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("ENVOYEE", "Envoyée"),
        ("VALIDEE", "Validée"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
        ("ANNULEE", "Annulée"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="proformas",
    )
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis",
        on_delete=models.CASCADE,
        related_name="proformas",
        null=True,
        blank=True,
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")
    date_emission = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class BonCommande(ValidationResponsableMixin):
    """Bon de commande emis simultanement a la facture des l'acceptation du
    devis : le client doit le signer electroniquement pour confirmer sa
    commande, condition prealable au paiement de la facture et donc au
    demarrage de la demande d'analyse."""

    STATUT_CHOICES = [
        ("EMIS", "Émis"),
        ("SIGNE_CLIENT", "Signé par le client"),
        ("ANNULE", "Annulé"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bons_commande")
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name="bons_commande")
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EMIS")
    date_emission = models.DateField(auto_now_add=True)

    # Signature electronique (dessinee) du client
    signature_client_image = models.ImageField(
        upload_to="facturation/signatures_client/", null=True, blank=True
    )
    date_signature_client = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class DemandeAnalyse(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE_ECHANTILLONS", "En attente d'échantillons"),
        ("ECHANTILLONS_RECUS", "Échantillons reçus"),
        ("EN_COURS", "En cours d'analyse"),
        ("TERMINEE", "Terminée"),
        ("RESULTATS_ENVOYES", "Résultats envoyés"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis",
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    proforma = models.ForeignKey(
        Proforma,
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    facture = models.ForeignKey(
        "Facture",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_analyses",
    )
    laboratoire = models.ForeignKey(
        "laboratoires.Laboratoire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_analyses",
    )
    statut = models.CharField(
        max_length=40,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE_ECHANTILLONS",
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_depot_echantillons = models.DateField(null=True, blank=True)
    date_debut_analyse = models.DateField(null=True, blank=True)
    date_fin_analyse = models.DateField(null=True, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class Facture(ValidationResponsableMixin):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_ATTENTE_VALIDATION", "En attente de validation comptable"),
        ("PAYEE", "Payée"),
        ("ANNULEE", "Annulée"),
    ]

    MODE_PAIEMENT_CHOICES = [
        ("CHEQUE", "Chèque"),
        ("COMPTANT", "Comptant"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="factures",
    )
    proforma = models.ForeignKey(
        Proforma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="factures",
    )
    bon_commande = models.ForeignKey(
        BonCommande,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="factures",
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default="EN_ATTENTE")
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    date_paiement = models.DateField(null=True, blank=True)

    # Informations de paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT_CHOICES,
        blank=True,
    )
    justificatif_paiement = models.FileField(
        upload_to="factures/paiements/",
        null=True,
        blank=True,
    )
    paiement_valide = models.BooleanField(default=False)
    visible_client = models.BooleanField(
        default=False,
        help_text="Quand vrai, la facture apparaît dans l'espace client",
    )
    reference_paiement = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
