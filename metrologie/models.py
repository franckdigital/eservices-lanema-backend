from django.contrib.auth.models import User
from django.db import models


class Equipement(models.Model):
    STATUT_CHOICES = [
        ("OPERATIONNEL", "Opérationnel"),
        ("ETALONNAGE_REQUIS", "Étalonnage requis"),
        ("MAINTENANCE", "Maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    TYPE_CHOICES = [
        ("BALANCE", "Balance"),
        ("ETUVE", "Étuve"),
        ("PRESSE", "Presse"),
        ("THERMOMETRE", "Thermomètre"),
        ("AUTRE", "Autre"),
    ]

    code = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="BALANCE")
    marque = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    date_dernier_etalonnage = models.DateField(null=True, blank=True)
    date_prochain_etalonnage = models.DateField(null=True, blank=True)
    localisation = models.CharField(max_length=255, blank=True)
    laboratoire = models.ForeignKey(
        "laboratoires.Laboratoire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipements",
    )
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipements_metrologie",
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OPERATIONNEL")

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class Etalonnage(models.Model):
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="etalonnages")
    date_etalonnage = models.DateField()
    date_prochain = models.DateField()
    prestataire = models.CharField(max_length=255, blank=True)
    resultat = models.CharField(max_length=50, default="CONFORME")

    def __str__(self) -> str:  # pragma: no cover
        return f"Etalonnage {self.equipement.code} - {self.date_etalonnage}"


class PanneEquipement(models.Model):
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="pannes")
    date_panne = models.DateField(auto_now_add=True)
    date_reparation = models.DateField(null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_panne"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Panne {self.equipement.code} - {self.date_panne}"


class MaintenancePreventive(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("REALISEE", "Réalisée"),
        ("REPORTEE", "Reportée"),
    ]

    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="maintenances_preventives")
    date_prevue = models.DateField()
    date_realisee = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    reussie = models.BooleanField(null=True, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_prevue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Maintenance {self.equipement.code} - {self.date_prevue}"


# ═══════════════════════════════════════════════════════════════════════════
# Circuit metrologie : service reception -> DMCT (travaux) -> certificat client
#   Fiche d'execution des travaux de metrologie (EN 004-PG 002) et Certificat
#   d'etalonnage (chaine nationale d'etalonnage).
# ═══════════════════════════════════════════════════════════════════════════

GRANDEURS = [
    ("TEMPERATURE", "Température"), ("PRESSION", "Pression"), ("MASSE", "Masse"), ("VOLUME", "Volume"),
    ("ELECTRICITE", "Électricité"), ("DIMENSIONNEL", "Dimensionnel"), ("AUTRE", "Autre"),
]
DECISIONS = [("CONFORME", "Conforme"), ("NON_CONFORME", "Non conforme"), ("SOUS_RESERVE", "Sous réserve")]


class FicheTravauxMetrologie(models.Model):
    """Fiche d'execution des travaux de metrologie (FET) — EN 004-PG 002 V06."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon (réception)"),
        ("TRANSMISE", "Transmise à la DMCT"),
        ("RECUE", "Reçue par la DMCT"),
        ("EN_COURS", "Travaux en cours"),
        ("TERMINEE", "Travaux terminés"),
        ("CLOTUREE", "Clôturée (certificats transmis)"),
    ]
    LIEU_CHOICES = [("LABORATOIRE", "Laboratoire"), ("SITE_CLIENT", "Site client")]

    numero = models.CharField(max_length=50, unique=True, help_text="Année/Direction/N° d'ordre")
    annee = models.PositiveIntegerField()
    direction = models.CharField(max_length=20, default="DMCT")
    demande_devis = models.ForeignKey("demandes.DemandeDevis", on_delete=models.CASCADE, related_name="fiches_metrologie")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")

    # PRESTATIONS (renseigne par la reception a partir du devis, ajustable par la DMCT)
    lieu_realisation = models.CharField(max_length=20, choices=LIEU_CHOICES, default="LABORATOIRE")
    operations_preliminaires = models.JSONField(default=list, blank=True, help_text="EXIGENCES_CLIENTS, DOCUMENTS_LANEMA, SPECS_CONSTRUCTEUR, DOCUMENTS_NORMATIFS")
    nombre_mesures_references = models.JSONField(default=list, blank=True, help_text="DOC_CLIENT, DOC_LANEMA, SPECS_CONSTRUCTEUR")
    definition_points = models.TextField(blank=True)
    observations_mesures = models.TextField(blank=True)
    erreurs_max_references = models.JSONField(default=list, blank=True, help_text="DOC_CLIENT, DOC_LANEMA, SPECS_CONSTRUCTEUR")
    jugement_references = models.JSONField(default=list, blank=True, help_text="DOC_CLIENT, SPECS_PARTICULIERES_CONSTRUCTEUR, DOCS_NORMATIFS")

    # Travaux au laboratoire
    date_arrivee_materiel = models.DateField(null=True, blank=True)
    date_transmission_dmct = models.DateTimeField(null=True, blank=True)
    receptionne_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    date_reception_dmct = models.DateTimeField(null=True, blank=True)
    date_debut_travaux = models.DateField(null=True, blank=True)
    date_fin_travaux = models.DateField(null=True, blank=True)
    # Travaux sur site client
    date_arrivee_site = models.DateField(null=True, blank=True)
    interlocuteur_site = models.CharField(max_length=255, blank=True)
    visa_site = models.CharField(max_length=255, blank=True)
    date_debut_site = models.DateField(null=True, blank=True)
    date_fin_site = models.DateField(null=True, blank=True)

    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class EquipementFTM(models.Model):
    """Equipement decrit sur la fiche ; son code (fiche d'entree) le suit jusqu'au certificat."""

    fiche = models.ForeignKey(FicheTravauxMetrologie, on_delete=models.CASCADE, related_name="equipements")
    fiche_entree = models.ForeignKey(
        "qualite.FicheEntreeEquipement", on_delete=models.SET_NULL, null=True, blank=True, related_name="equipements_ftm"
    )
    code = models.CharField(max_length=100, blank=True, help_text="Code de la fiche d'entrée (suit l'équipement jusqu'au certificat)")
    designation = models.CharField(max_length=255)
    constructeur = models.CharField(max_length=255, blank=True)
    modele = models.CharField(max_length=255, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    nature = models.CharField(max_length=100, blank=True, help_text="Étalonnage, Vérification, ...")
    grandeur = models.CharField(max_length=20, choices=GRANDEURS, default="AUTRE")
    plage_mesure = models.CharField(max_length=100, blank=True)
    resolution = models.CharField(max_length=50, blank=True)
    classe = models.CharField(max_length=50, blank=True)
    unite = models.CharField(max_length=30, blank=True)
    localisation = models.CharField(max_length=255, blank=True)
    decision = models.CharField(max_length=20, choices=DECISIONS, blank=True)
    reserves = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "id"]


class CertificatEtalonnage(models.Model):
    """Certificat d'etalonnage d'un instrument (un certificat par equipement)."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("EDITE", "Édité"),
        ("SIGNE", "Signé"),
        ("TRANSMIS", "Transmis au client"),
    ]

    equipement = models.OneToOneField(EquipementFTM, on_delete=models.CASCADE, related_name="certificat")
    fiche = models.ForeignKey(FicheTravauxMetrologie, on_delete=models.CASCADE, related_name="certificats")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")
    annee = models.PositiveIntegerField(null=True, blank=True)
    numero_ordre = models.PositiveIntegerField(null=True, blank=True)
    numero = models.CharField(max_length=60, blank=True, db_index=True, help_text="CE N°")
    grandeur = models.CharField(max_length=20, choices=GRANDEURS, default="AUTRE")
    accredite = models.BooleanField(default=False, help_text="Étalonnage sous accréditation SOAC (température, pression)")
    date_etalonnage = models.DateField(null=True, blank=True)
    date_emission = models.DateField(null=True, blank=True)
    conditions = models.JSONField(default=dict, blank=True, help_text="temperature, humidite, pression_atmospherique")
    methode = models.TextField(blank=True)
    etalons_utilises = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    directeur_nom = models.CharField(max_length=255, blank=True)
    operateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edite_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    date_signature = models.DateField(null=True, blank=True)
    date_transmission = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-annee", "-numero_ordre", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["annee", "numero_ordre"], name="certificat_etalonnage_numero_unique_par_annee"),
        ]


class PointEtalonnage(models.Model):
    """Point de mesure du certificat : valeur de l'etalon, indication de l'instrument, ecart, incertitude."""

    certificat = models.ForeignKey(CertificatEtalonnage, on_delete=models.CASCADE, related_name="points")
    ordre = models.PositiveIntegerField(default=0)
    valeur_etalon = models.CharField(max_length=50)
    valeur_instrument = models.CharField(max_length=50)
    ecart = models.CharField(max_length=50, blank=True)
    incertitude = models.CharField(max_length=50, blank=True, help_text="Incertitude élargie U (k=2)")
    unite = models.CharField(max_length=30, blank=True)
    conforme = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["ordre", "id"]
