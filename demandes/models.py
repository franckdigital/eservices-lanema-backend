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

    LIEU_REALISATION_CHOICES = [
        ("LABORATOIRE", "Laboratoire"),
        ("SITE_CLIENT", "Site client"),
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

    # Champs restants du formulaire officiel EN 002-PG002, non repris ailleurs :
    # "Le laboratoire doit-il gerer le renvoi du materiel", "Lieu de realisation
    # des Travaux", "Observations particulieres", "Declaration de Conformite"
    # + "Regle de decision" (cette derniere renseignee par le service reception
    # lors de la finalisation du devis officiel).
    retour_materiel_gere_labo = models.BooleanField(
        null=True, blank=True, help_text="Le laboratoire doit-il gerer le renvoi du materiel (metrologie)"
    )
    lieu_realisation = models.CharField(
        max_length=20, choices=LIEU_REALISATION_CHOICES, default="LABORATOIRE"
    )
    observations_particulieres = models.TextField(blank=True)
    declaration_conformite_souhaitee = models.BooleanField(null=True, blank=True)
    regle_decision = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class InterventionPrelevement(models.Model):
    """Ligne du tableau "2 - Prélèvement ou récupération de l'appareil de
    mesure" du formulaire officiel EN 002-PG002 — designations fixes,
    renseignees par le service reception lors de la finalisation du devis
    (duree, kilometrage, nombre et prix unitaire), avant envoi au client."""

    DESIGNATION_CHOICES = [
        ("INGENIEUR", "Intervention d'un ingénieur"),
        ("TECHNICIEN", "Intervention d'un technicien"),
        ("CHAUFFEUR", "Intervention d'un chauffeur"),
        ("VEHICULE", "Coût du véhicule d'intervention"),
        ("DEPLACEMENT", "Coût de déplacement"),
    ]

    demande = models.ForeignKey(
        DemandeDevis, on_delete=models.CASCADE, related_name="interventions_prelevement"
    )
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES)
    duree_heures = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    nombre = models.PositiveIntegerField(default=0)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ("demande", "designation")
        ordering = ["id"]

    @property
    def montant(self):
        return (self.prix_unitaire or 0) * (self.nombre or 0)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_designation_display()} ({self.demande.numero})"


class EchantillonPrevu(models.Model):
    """Echantillon annonce par le client au moment de la demande de devis
    (nom + quantite) : liste de reference pour le service reception, qui
    cree l'echantillon reel (qualite.Echantillon, avec code de tracabilite)
    une fois le devis signe et l'echantillon physiquement receptionne."""

    demande = models.ForeignKey(DemandeDevis, on_delete=models.CASCADE, related_name="echantillons_prevus")
    nom = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField(default=1)

    # Renseignes par le service reception lors de la finalisation du devis
    # officiel : correspond a la ligne "Paramètres ou Grandeurs / Méthodes
    # utilisées / P.U. / Nombre / Montant" du formulaire EN 002-PG002.
    methode_utilisee = models.CharField(max_length=255, blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sous_traite = models.BooleanField(default=False, help_text="Prestation sous-traitee (mention 'ST' sur le devis)")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.nom} x{self.quantite} ({self.demande.numero})"
