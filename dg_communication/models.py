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
    """Enquête de satisfaction ponctuelle liée aux actions marketing/commerciales.

    Saisie manuellement par un agent après avoir recueilli l'avis du client
    par un autre canal (téléphone, email, entretien...) — pas encore un
    sondage self-service envoyé directement au client."""

    CANAL_CHOICES = [
        ("TELEPHONE", "Téléphone"),
        ("EMAIL", "Email"),
        ("ENTRETIEN", "Entretien en personne"),
        ("FORMULAIRE", "Formulaire papier"),
        ("AUTRE", "Autre"),
    ]

    client_nom = models.CharField(max_length=255)
    organisation = models.CharField(max_length=255, blank=True, help_text="Entreprise/structure du client")
    contact_email = models.EmailField(blank=True)
    contact_telephone = models.CharField(max_length=50, blank=True)
    action_liee = models.ForeignKey(
        ActionCommunication, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="enquetes_satisfaction",
        help_text="Action/campagne à l'origine de la relation avec ce client, le cas échéant",
    )
    service_concerne = models.CharField(
        max_length=255, blank=True, help_text="Prestation ou service concerné par cette enquête"
    )
    canal_recueil = models.CharField(
        max_length=20, choices=CANAL_CHOICES, blank=True,
        help_text="Comment l'avis du client a été recueilli",
    )
    recueilli_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="enquetes_satisfaction_recueillies",
        help_text="Agent ayant recueilli et saisi cet avis",
    )
    note = models.PositiveSmallIntegerField(help_text="Note sur 5")
    recommanderait = models.BooleanField(
        null=True, blank=True, help_text="Le client recommanderait-il le LANEMA ? (laisser vide si non demandé)"
    )
    fidele = models.BooleanField(default=False, help_text="Client fidélisé (renouvellement)")
    commentaire = models.TextField(blank=True)
    date_enquete = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_enquete"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client_nom} ({self.note}/5)"
