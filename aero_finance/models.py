from decimal import Decimal

from django.db import models

from aero_clients.models import ClientAeronautique
from aero_maintenance.models import OrdreTravail

# Taux horaire main d'oeuvre DAE (FCFA/heure), utilise pour le calcul
# automatique de la facturation a partir du temps reellement passe
# (InterventionTechnique.temps_passe_minutes) — cf. cahier des charges
# section 20 et 32.
TAUX_HORAIRE_DAE = Decimal("5000")


class DevisDAE(models.Model):
    """Devis (estimation), en amont de l'ordre de travail — montants saisis
    manuellement puisque le travail n'a pas encore ete realise (contrairement
    a la facture, qui peut etre generee automatiquement depuis les donnees
    reelles une fois l'OT termine)."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("ENVOYE", "Envoyé"),
        ("ACCEPTE", "Accepté"),
        ("REFUSE", "Refusé"),
        ("EXPIRE", "Expiré"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="devis"
    )
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="devis")
    description = models.TextField(blank=True)
    montant_main_oeuvre = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_pieces = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    frais_supplementaires = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="BROUILLON")
    date_creation = models.DateField(auto_now_add=True)
    date_validite = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    @property
    def montant_ht(self):
        return self.montant_main_oeuvre + self.montant_pieces + self.frais_supplementaires

    @property
    def montant_ttc(self):
        return round(self.montant_ht * (1 + self.taux_tva / 100), 2)


class BonCommandeDAE(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente de signature"),
        ("SIGNE", "Signé"),
        ("ANNULE", "Annulé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    devis = models.ForeignKey(DevisDAE, on_delete=models.SET_NULL, null=True, blank=True, related_name="bons_commande")
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="bons_commande"
    )
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="bons_commande")
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="EN_ATTENTE")
    date_creation = models.DateField(auto_now_add=True)
    date_signature = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


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
    bon_commande = models.ForeignKey(
        BonCommandeDAE, on_delete=models.SET_NULL, null=True, blank=True, related_name="factures"
    )
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="factures")

    # Décomposition (cf. cahier des charges section 20 : main d'œuvre +
    # pièces + prestations + frais supplémentaires = montant total). Les
    # montants sont soit saisis manuellement, soit calculés automatiquement
    # depuis l'OT via l'action generer_depuis_ot (temps reel des
    # interventions x taux horaire + prix des pieces reellement utilisees).
    montant_main_oeuvre = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_pieces = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    frais_supplementaires = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=18)

    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="EMISE")
    date_emission = models.DateField(auto_now_add=True)
    date_paiement = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def recalculer_totaux(self):
        self.montant_ht = self.montant_main_oeuvre + self.montant_pieces + self.frais_supplementaires
        self.montant_ttc = round(self.montant_ht * (1 + self.taux_tva / 100), 2)
