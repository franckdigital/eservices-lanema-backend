from django.contrib.auth.models import User
from django.db import models


class CreneauDisponibilite(models.Model):
    """Plage de dates pendant laquelle le laboratoire annonce un delai de
    realisation donne — parametree depuis l'espace du service reception,
    affichee sur le formulaire public de demande de devis (cf. cahier des
    charges EN 002-PG002, champ "Delais de realisation")."""

    date_debut = models.DateField()
    date_fin = models.DateField()
    delai_jours_ouvres = models.PositiveIntegerField(help_text="Delai de realisation annonce, en jours ouvres")
    label = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.date_debut} -> {self.date_fin} ({self.delai_jours_ouvres}j)"


class SousTraitantPartenaire(models.Model):
    """Sous-traitant pouvant etre associe a une demande de devis : soit un
    partenaire officiel du catalogue LANEMA (choisi directement par le client
    sur le formulaire public), soit un sous-traitant souhaite par un client et
    formalise dans le catalogue par le service reception apres examen de sa
    demande libre (cf. DemandeDevis.sous_traitants_souhaits_libres)."""

    TYPE_CHOICES = [
        ("PARTENAIRE", "Partenaire officiel LANEMA"),
        ("CLIENT", "Proposé par un client"),
    ]

    nom = models.CharField(max_length=255)
    specialite = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    type_sous_traitant = models.CharField(max_length=20, choices=TYPE_CHOICES, default="PARTENAIRE")
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class DemandeDevis(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_COURS", "En cours"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="demandes_devis",
    )
    type_analyse = models.CharField(max_length=255)
    categorie = models.CharField(max_length=255, blank=True)
    objet = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    created_at = models.DateTimeField(auto_now_add=True)

    # Delai de realisation annonce au client, fige au moment de la demande
    # (cf. CreneauDisponibilite active a cette date).
    delai_realisation_jours = models.PositiveIntegerField(null=True, blank=True)

    # Sous-traitance (cf. cahier des charges EN 002-PG002, "Accord de Sous-traitance")
    accord_sous_traitance = models.BooleanField(default=False)
    sous_traitants_choisis = models.ManyToManyField(
        SousTraitantPartenaire, blank=True, related_name="demandes_devis"
    )
    sous_traitants_souhaits_libres = models.TextField(
        blank=True, help_text="Sous-traitants hors catalogue, souhaites librement par le client"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class EchantillonPrevu(models.Model):
    """Echantillon annonce par le client au moment de la demande de devis
    (nom + quantite) : liste de reference pour le service reception, qui
    cree l'echantillon reel (qualite.Echantillon, avec code de tracabilite)
    une fois le devis signe et l'echantillon physiquement receptionne."""

    demande = models.ForeignKey(DemandeDevis, on_delete=models.CASCADE, related_name="echantillons_prevus")
    nom = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.nom} x{self.quantite} ({self.demande.numero})"
