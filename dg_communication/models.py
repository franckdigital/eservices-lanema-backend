from django.contrib.auth.models import User
from django.db import models


class ActionCommunication(models.Model):
    """Action de communication ou marketing (campagne, communiqué, événement, salon, support)."""

    TYPE_CHOICES = [
        ("CAMPAGNE", "Campagne de communication"),
        ("COMMUNIQUE", "Communiqué de presse"),
        ("EVENEMENT", "Événement"),
        ("SALON", "Salon / foire"),
        ("SUPPORT", "Support de communication"),
    ]
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("EN_COURS", "En cours"),
        ("REALISEE", "Réalisée"),
        ("ANNULEE", "Annulée"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    chiffre_affaires_genere = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_communication"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} - {self.titre}"


class Prospect(models.Model):
    """Prospect généré par une action marketing, suivi jusqu'à conversion en client."""

    STATUT_CHOICES = [
        ("NOUVEAU", "Nouveau"),
        ("QUALIFIE", "Qualifié"),
        ("DEVIS_ENVOYE", "Devis envoyé"),
        ("CONVERTI", "Converti en client"),
        ("PERDU", "Perdu"),
    ]

    nom = models.CharField(max_length=255)
    organisation = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_telephone = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    action_origine = models.ForeignKey(
        ActionCommunication, on_delete=models.SET_NULL, null=True, blank=True, related_name="prospects"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="NOUVEAU")
    montant_devis = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_conversion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class Partenariat(models.Model):
    STATUT_CHOICES = [
        ("EN_NEGOCIATION", "En négociation"),
        ("ACTIF", "Actif"),
        ("TERMINE", "Terminé"),
    ]

    nom_partenaire = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_signature = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_NEGOCIATION")
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="partenariats"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom_partenaire


class SatisfactionClient(models.Model):
    """Enquête de satisfaction ponctuelle liée aux actions marketing/commerciales."""

    client_nom = models.CharField(max_length=255)
    note = models.PositiveSmallIntegerField(help_text="Note sur 5")
    fidele = models.BooleanField(default=False, help_text="Client fidélisé (renouvellement)")
    commentaire = models.TextField(blank=True)
    date_enquete = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_enquete"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client_nom} ({self.note}/5)"
