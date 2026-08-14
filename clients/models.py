from django.contrib.auth.models import User
from django.db import models


class ClientProfile(models.Model):
    """Profil metier (module laboratoire) associe a un utilisateur Django :
    role client/fournisseur/staff labo, coordonnees commerciales, notifications push.

    Remplace l'ancien modele clients.User (AUTH_USER_MODEL du projet labo) : ce
    projet utilise deja django.contrib.auth.User, donc ces champs deviennent un
    profil OneToOne au lieu d'un modele utilisateur personnalise."""

    ROLE_CHOICES = [
        ("ADMIN", "Administrateur"),
        ("GESTIONNAIRE", "Gestionnaire"),
        ("TECHNICIEN", "Technicien"),
        ("CLIENT", "Client"),
        ("FOURNISSEUR", "Fournisseur"),
        ("COMPTABLE", "Comptable"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="CLIENT")
    type_subscription = models.CharField(max_length=50, blank=True)
    organisation = models.CharField(max_length=255, blank=True)

    # Champs pour la gestion des clients (admin dashboard)
    raison_sociale = models.CharField(max_length=255, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    siret = models.CharField(max_length=50, blank=True)
    contact_nom = models.CharField(max_length=255, blank=True)
    expo_push_token = models.CharField(max_length=255, blank=True, null=True)

    # Signature et cachet du responsable labo (roles ADMIN/GESTIONNAIRE), reutilises
    # pour valider les devis, bons de commande et factures sans les redemander a chaque fois.
    signature_image = models.ImageField(upload_to="clients/signatures_responsable/", null=True, blank=True)
    cachet_image = models.ImageField(upload_to="clients/cachets_responsable/", null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.user.username} ({self.role})"


class LaboRolePermission(models.Model):
    """Octroi d'une permission (code de module.action) a un role du personnel
    labo (ClientProfile.role). Pilote la navigation et l'acces aux routes du
    portail staff /app ; editable via l'ecran Administration > Permissions.

    Le role ADMIN est toujours considere comme ayant tous les droits (cf.
    clients.permissions_catalog.user_permission_codes), independamment des
    lignes presentes ici, pour eviter tout risque de verrouillage."""

    role = models.CharField(max_length=20, choices=ClientProfile.ROLE_CHOICES)
    permission_code = models.CharField(max_length=100)
    is_granted = models.BooleanField(default=True)

    class Meta:
        unique_together = ("role", "permission_code")
        ordering = ["role", "permission_code"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.role} - {self.permission_code} ({'accorde' if self.is_granted else 'refuse'})"


class ReclamationClient(models.Model):
    """Reclamation d'un client du laboratoire (distincte de dg_qualite.ReclamationClient,
    qui est organisationnelle/DAAF ; celle-ci est specifique au service rendu par le labo)."""

    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("TRAITEE", "Traitée"),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reclamations_labo")
    description = models.TextField()
    date_reception = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5, apres resolution")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client.username} - {self.date_reception}"
