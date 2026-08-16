import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ClientAeronautique(models.Model):
    """`nom` sert de raison sociale. Cf. cahier des charges section 5 :
    code, type de client, coordonnées et personne responsable distincts."""

    TYPE_CHOICES = [
        ("COMPAGNIE_AERIENNE", "Compagnie aérienne"),
        ("FORCES_ARMEES", "Forces armées"),
        ("ADMINISTRATION", "Administration"),
        ("SOCIETE_MAINTENANCE", "Société de maintenance aéronautique"),
        ("AEROCLUB", "Aéroclub"),
        ("OPERATEUR_PRIVE", "Opérateur privé"),
        ("ORGANISME_PUBLIC", "Organisme public"),
        ("AUTRE", "Autre"),
    ]

    code = models.CharField(max_length=30, unique=True, blank=True)
    nom = models.CharField(max_length=255, unique=True)
    type_client = models.CharField(max_length=25, choices=TYPE_CHOICES, default="AUTRE")
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    numero_identification = models.CharField(max_length=100, blank=True, help_text="RCCM, NIF ou équivalent")
    contact = models.CharField(max_length=255, blank=True, help_text="Personne responsable")
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    compte_utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="client_aeronautique",
        help_text="Compte du portail client DAE lié à cette organisation (cf. cahier des charges section 3.7)",
    )

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom

    def save(self, *args, **kwargs):
        if not self.code:
            last = ClientAeronautique.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.code = f"CLI-DAE-{num:04d}"
        super().save(*args, **kwargs)


class Aeronef(models.Model):
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_MAINTENANCE", "En maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    immatriculation = models.CharField(max_length=50, unique=True)
    type_aeronef = models.CharField(max_length=255, blank=True)
    constructeur = models.CharField(max_length=255, blank=True)
    modele = models.CharField(max_length=255, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    proprietaire = models.CharField(max_length=255, blank=True, help_text="Si différent de l'exploitant (client)")
    annee_fabrication = models.PositiveIntegerField(null=True, blank=True)
    nombre_heures_vol = models.PositiveIntegerField(default=0)
    nombre_cycles = models.PositiveIntegerField(default=0)
    client = models.ForeignKey(
        ClientAeronautique, on_delete=models.SET_NULL, null=True, blank=True, related_name="aeronefs",
        help_text="Exploitant"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")

    class Meta:
        ordering = ["immatriculation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.immatriculation


class ReclamationClientDAE(models.Model):
    """Reclamation d'un client de la Direction de l'Aeronautique (distincte de
    clients.ReclamationClient et dg_qualite.ReclamationClient, memes principes
    de separation par domaine deja etablis). Cf. cahier des charges section 22,
    workflow : Enregistrement -> Analyse -> Affectation -> Traitement ->
    Reponse -> Cloture (verrouille via ReclamationClientDAEViewSet.changer_statut)."""

    TYPE_CHOICES = [
        ("RETARD", "Retard"),
        ("PROBLEME_TECHNIQUE", "Problème technique"),
        ("PROBLEME_ADMINISTRATIF", "Problème administratif"),
        ("PROBLEME_FACTURATION", "Problème de facturation"),
        ("QUALITE_INSUFFISANTE", "Qualité insuffisante"),
        ("AUTRE", "Autre"),
    ]
    STATUT_CHOICES = [
        ("ENREGISTREE", "Enregistrée"),
        ("EN_ANALYSE", "En analyse"),
        ("AFFECTEE", "Affectée"),
        ("EN_TRAITEMENT", "En traitement"),
        ("REPONSE_ENVOYEE", "Réponse envoyée"),
        ("CLOTUREE", "Clôturée"),
    ]

    reference = models.CharField(max_length=50, unique=True, blank=True)
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="reclamations")
    ordre_travail = models.ForeignKey(
        "aero_maintenance.OrdreTravail", on_delete=models.SET_NULL, null=True, blank=True, related_name="reclamations"
    )
    type_reclamation = models.CharField(max_length=25, choices=TYPE_CHOICES, default="AUTRE")
    description = models.TextField()
    analyse = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reclamations_dae"
    )
    reponse = models.TextField(blank=True)
    date_reception = models.DateField(auto_now_add=True)
    date_reponse = models.DateField(null=True, blank=True)
    date_traitement = models.DateField(null=True, blank=True, help_text="Date de clôture")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="ENREGISTREE")
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            year = timezone.now().year
            last = ReclamationClientDAE.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"RECL-DAE-{year}-{num:05d}"
        super().save(*args, **kwargs)


class SatisfactionDAE(models.Model):
    """Fiche de satisfaction post-intervention, accessible par lien public
    (token, sans compte) — cf. cahier des charges section 21 : qualité,
    délai, accueil, communication, prestation technique, chacun noté sur 5."""

    ordre_travail = models.OneToOneField(
        "aero_maintenance.OrdreTravail", on_delete=models.CASCADE, related_name="satisfaction"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    note_qualite = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    note_delai = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    note_accueil = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    note_communication = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    note_prestation_technique = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    commentaire = models.TextField(blank=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    date_evaluation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_envoi"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Satisfaction {self.ordre_travail.reference}"

    @property
    def note_moyenne(self):
        notes = [
            n for n in [
                self.note_qualite, self.note_delai, self.note_accueil,
                self.note_communication, self.note_prestation_technique,
            ] if n is not None
        ]
        return round(sum(notes) / len(notes), 2) if notes else None


class DemandeDAE(models.Model):
    """Demande de prestation d'un client, avant transformation en Ordre de
    travail (aero_maintenance.OrdreTravail) apres acceptation — etape
    manquante du cahier des charges : jusqu'ici, l'OT etait cree directement
    sans etape de validation prealable."""

    TYPE_CHOICES = [
        ("PREVENTIVE", "Maintenance préventive"),
        ("CORRECTIVE", "Maintenance corrective"),
        ("URGENCE", "Urgence"),
    ]
    URGENCE_CHOICES = [
        ("NORMALE", "Normale"),
        ("HAUTE", "Haute"),
        ("URGENTE", "Urgente"),
    ]
    STATUT_CHOICES = [
        ("NOUVELLE", "Nouvelle"),
        ("A_ETUDIER", "À étudier"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
        ("EN_TRAITEMENT", "En traitement"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="demandes")
    aeronef = models.ForeignKey(
        Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes"
    )
    type_intervention = models.CharField(max_length=20, choices=TYPE_CHOICES, default="CORRECTIVE")
    description = models.TextField(blank=True)
    urgence = models.CharField(max_length=10, choices=URGENCE_CHOICES, default="NORMALE")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="NOUVELLE")
    date_reception = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    ordre_travail = models.OneToOneField(
        "aero_maintenance.OrdreTravail",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="demande",
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
