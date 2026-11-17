from django.contrib.auth.models import User
from django.db import models


class TypeEchantillon(models.Model):
    """Types d'échantillons (Microbiologie, Eaux, etc.)"""
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Echantillon(models.Model):
    """Modèle pour les échantillons du laboratoire"""
    STATUT_CHOICES = [
        ("RECEPTIONNE", "Réceptionné"),
        ("EN_ATTENTE", "En attente"),
        ("EN_ANALYSE", "En analyse"),
        ("TERMINE", "Terminé"),
        ("REJETE", "Rejeté"),
        ("ARCHIVE", "Archivé"),
    ]

    code_echantillon = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    type_echantillon = models.CharField(max_length=100, blank=True, default='')
    demande = models.ForeignKey(
        'facturation.DemandeAnalyse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="echantillons",
        help_text="Demande d'analyse (le paiement doit etre valide avant reception des echantillons)",
    )
    quantite = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="RECEPTIONNE")
    conforme = models.BooleanField(
        null=True, blank=True,
        help_text="Conformite de l'echantillon suite a analyse (null = pas encore evalue)"
    )
    date_reception = models.DateField()
    emplacement_stockage = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Informations de la fiche d'execution des travaux d'essais (EN 003-PG 002)
    # et du rapport d'essai (EN 001-PG019) : le meme code suit l'echantillon de
    # la reception jusqu'au rapport.
    fiche = models.ForeignKey(
        "qualite.FicheExecutionTravaux", on_delete=models.SET_NULL, null=True, blank=True, related_name="echantillons"
    )
    date_prelevement = models.DateField(null=True, blank=True)
    date_heure_prelevement = models.DateTimeField(null=True, blank=True)
    lieu_prelevement = models.CharField(max_length=255, blank=True)
    prelevement_par = models.CharField(max_length=255, blank=True)
    numero_lot = models.CharField(max_length=100, blank=True)
    date_heure_arrivee = models.DateTimeField(null=True, blank=True)
    etat = models.JSONField(default=list, blank=True, help_text="SOLIDE, LIQUIDE, POUDRE, PATE, CRISTAUX, AUTRES")
    etat_precision = models.CharField(max_length=255, blank=True)
    parametres = models.TextField(blank=True, help_text="Parametres a analyser")
    laboratoires = models.ManyToManyField("laboratoires.Laboratoire", blank=True, related_name="echantillons_concernes")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code_echantillon

    def save(self, *args, **kwargs):
        if not self.code_echantillon:
            # Auto-generate code
            from django.utils import timezone
            today = timezone.now()
            prefix = f"ECH-{today.strftime('%Y%m%d')}"
            last = Echantillon.objects.filter(code_echantillon__startswith=prefix).order_by('-code_echantillon').first()
            if last:
                try:
                    num = int(last.code_echantillon.split('-')[-1]) + 1
                except:
                    num = 1
            else:
                num = 1
            self.code_echantillon = f"{prefix}-{num:03d}"
        super().save(*args, **kwargs)


class FicheEntreeEquipement(models.Model):
    """Fiche d'entree des equipements/instruments recus au service reception
    pour la metrologie (etalonnage) ou l'aeronautique — mecanisme volontairement
    simple et generique, a personnaliser plus tard par domaine. Pendant de
    Echantillon (essais/analyses), mais pour du materiel client au lieu
    d'echantillons consommables."""

    DOMAINE_CHOICES = [
        ("METROLOGIE", "Métrologie"),
        ("AERONAUTIQUE", "Aéronautique"),
    ]
    STATUT_CHOICES = [
        ("RECEPTIONNE", "Réceptionné"),
        ("TRANSMIS_LABO", "Transmis au laboratoire/atelier"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("RESTITUE", "Restitué au client"),
    ]

    code = models.CharField(max_length=100, unique=True)
    domaine = models.CharField(max_length=20, choices=DOMAINE_CHOICES)
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fiches_entree_equipement", help_text="Pour une fiche du domaine METROLOGIE",
    )
    demande_dae = models.ForeignKey(
        "aero_clients.DemandeDAE", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fiches_entree_equipement", help_text="Pour une fiche du domaine AERONAUTIQUE",
    )
    designation = models.CharField(max_length=255)
    marque = models.CharField(max_length=255, blank=True)
    modele = models.CharField(max_length=255, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    etat_reception = models.CharField(max_length=255, blank=True, help_text="Etat constate a la reception")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="RECEPTIONNE")
    date_reception = models.DateField()
    recu_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils import timezone
            today = timezone.now()
            prefix = f"FE-{today.strftime('%Y%m%d')}"
            last = FicheEntreeEquipement.objects.filter(code__startswith=prefix).order_by('-code').first()
            if last:
                try:
                    num = int(last.code.split('-')[-1]) + 1
                except Exception:
                    num = 1
            else:
                num = 1
            self.code = f"{prefix}-{num:03d}"
        super().save(*args, **kwargs)


class Essai(models.Model):
    """Modèle pour les essais/analyses du laboratoire"""
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("VALIDE", "Validé"),
        ("ANNULE", "Annulé"),
    ]

    numero = models.CharField(max_length=100, unique=True)
    type_essai = models.CharField(max_length=100, blank=True)
    echantillon = models.ForeignKey(
        Echantillon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="essais",
    )
    laboratoire = models.ForeignKey(
        "laboratoires.Laboratoire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="essais",
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    date_debut = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True, help_text="Date reelle de fin de l'essai")
    technicien = models.CharField(max_length=255, blank=True)
    technicien_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="essais_technicien",
    )
    urgent = models.BooleanField(default=False)
    est_reprise = models.BooleanField(default=False)
    essai_origine = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reprises",
    )
    erreur_detectee = models.BooleanField(default=False)
    cout_revient = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    norme = models.CharField(max_length=255, blank=True)
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.numero

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone
            today = timezone.now()
            prefix = f"ESS-{today.strftime('%Y%m%d')}"
            last = Essai.objects.filter(numero__startswith=prefix).order_by('-numero').first()
            if last:
                try:
                    num = int(last.numero.split('-')[-1]) + 1
                except:
                    num = 1
            else:
                num = 1
            self.numero = f"{prefix}-{num:03d}"
        super().save(*args, **kwargs)


class NonConformite(models.Model):
    TYPE_CHOICES = [
        ("INTERNE", "Interne"),
        ("EXTERNE", "Externe"),
    ]
    GRAVITE_CHOICES = [
        ("MINEURE", "Mineure"),
        ("MAJEURE", "Majeure"),
        ("CRITIQUE", "Critique"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    type_nc = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INTERNE")
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, default="MINEURE")
    description = models.TextField()
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="non_conformites",
    )
    essai = models.ForeignKey(
        Essai,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="non_conformites",
    )
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.numero

    def save(self, *args, **kwargs):
        if not self.numero:
            last = NonConformite.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.numero = f"NC-{num:03d}"
        super().save(*args, **kwargs)


class Audit(models.Model):
    TYPE_CHOICES = [
        ("INTERNE", "Interne"),
        ("EXTERNE", "Externe"),
    ]

    reference = models.CharField(max_length=100, unique=True)
    type_audit = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INTERNE")
    organisme = models.CharField(max_length=255, blank=True)
    date_audit = models.DateField()
    resultat = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class ActionQualite(models.Model):
    TYPE_CHOICES = [
        ("CORRECTIVE", "Corrective"),
        ("PREVENTIVE", "Préventive"),
    ]
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("EN_COURS", "En cours"),
        ("CLOTUREE", "Clôturée"),
    ]

    non_conformite = models.ForeignKey(
        NonConformite, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_qualite_labo")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    date_planification = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_planification"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} - {self.description[:40]}"


class RecommandationAudit(models.Model):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="recommandations")
    description = models.TextField()
    appliquee = models.BooleanField(default=False)
    date_echeance = models.DateField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Recommandation {self.audit.reference}"


# ═══════════════════════════════════════════════════════════════════════════
# Circuit service reception <-> laboratoire
#   Fiche d'execution des travaux d'essais (EN 003-PG 002, redigee par la
#   reception) -> resultats saisis par le laboratoire -> rapport d'essai
#   (EN 001-PG019, edite par la reception, numero d'ordre chronologique).
# ═══════════════════════════════════════════════════════════════════════════

class CompteurSequence(models.Model):
    """Compteur sequentiel (verrouille a l'increment) : numeros de fiches par
    annee/direction et numeros d'ordre chronologiques des rapports d'essai."""

    cle = models.CharField(max_length=100, unique=True)
    valeur = models.PositiveIntegerField(default=0)

    @classmethod
    def suivant(cls, cle):
        from django.db import transaction

        with transaction.atomic():
            compteur, _ = cls.objects.select_for_update().get_or_create(cle=cle)
            compteur.valeur += 1
            compteur.save(update_fields=["valeur"])
            return compteur.valeur


class FicheExecutionTravaux(models.Model):
    """Fiche d'execution des travaux d'essais (FET) — EN 003-PG 002."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon (réception)"),
        ("TRANSMISE", "Transmise au laboratoire"),
        ("RECUE_LABO", "Reçue par le laboratoire"),
        ("RESULTATS_TRANSMIS", "Résultats transmis à la réception"),
        ("RESULTATS_RECUS", "Résultats reçus — rapport en préparation"),
        ("CLOTUREE", "Clôturée (rapports remis)"),
    ]
    NATURE_CHOICES = [
        ("ALIMENTAIRE", "Produits alimentaires"),
        ("INDUSTRIEL", "Produits industriels"),
        ("EAUX", "Eaux"),
        ("AUTRES", "Autres"),
    ]
    ACCEPTATION_CHOICES = [("CONFORME", "Conforme"), ("SOUS_RESERVE", "Sous réserve")]

    numero = models.CharField(max_length=50, unique=True, help_text="Année/Direction/N° d'ordre")
    annee = models.PositiveIntegerField()
    direction = models.CharField(max_length=20, blank=True)
    demande = models.ForeignKey("facturation.DemandeAnalyse", on_delete=models.CASCADE, related_name="fiches_travaux")
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default="BROUILLON")
    nature_objet = models.CharField(max_length=20, choices=NATURE_CHOICES, default="ALIMENTAIRE")
    nature_precision = models.CharField(max_length=255, blank=True)
    date_arrivee_lanema = models.DateField(null=True, blank=True)
    date_transmission_laboratoire = models.DateTimeField(null=True, blank=True)
    delai_realisation = models.CharField(max_length=255, blank=True)
    observations = models.TextField(blank=True)
    # Reception (SRO) des resultats / du rapport transmis par le laboratoire
    re_receptionne_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    date_reception_re = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class FETLaboratoire(models.Model):
    """Suivi d'une fiche par laboratoire concerne : reception, acceptation des
    echantillons, transmission des resultats."""

    STATUT_CHOICES = [
        ("TRANSMIS", "Transmis"),
        ("RECU", "Reçu — en analyse"),
        ("RESULTATS_TRANSMIS", "Résultats transmis"),
    ]

    fiche = models.ForeignKey(FicheExecutionTravaux, on_delete=models.CASCADE, related_name="suivis_labo")
    laboratoire = models.ForeignKey("laboratoires.Laboratoire", on_delete=models.CASCADE, related_name="suivis_fiches")
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default="TRANSMIS")
    date_reception = models.DateTimeField(null=True, blank=True)
    receptionne_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    acceptation = models.CharField(max_length=20, choices=FicheExecutionTravaux.ACCEPTATION_CHOICES, blank=True)
    reserves = models.TextField(blank=True)
    date_transmission_resultats = models.DateTimeField(null=True, blank=True)
    transmis_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        unique_together = ("fiche", "laboratoire")
        ordering = ["laboratoire__code"]


class ResultatEssai(models.Model):
    """Resultat d'un parametre pour un echantillon, saisi par le laboratoire."""

    echantillon = models.ForeignKey(Echantillon, on_delete=models.CASCADE, related_name="resultats")
    laboratoire = models.ForeignKey("laboratoires.Laboratoire", on_delete=models.CASCADE, related_name="resultats")
    parametre = models.CharField(max_length=255)
    methode = models.CharField(max_length=255, blank=True)
    unite = models.CharField(max_length=50, blank=True)
    resultat = models.CharField(max_length=255)
    specification = models.CharField(max_length=255, blank=True, help_text="Limite / critère d'acceptation")
    conforme = models.BooleanField(null=True, blank=True, help_text="null = sans objet")
    accredite = models.BooleanField(default=False, help_text="Essai sous accréditation : résultat en gras (**)")
    sous_traite = models.BooleanField(default=False, help_text="Essai sous-traité : symbole S/T")
    ordre = models.PositiveIntegerField(default=0)
    analyste = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    date_analyse = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["echantillon_id", "ordre", "id"]


class RapportEssaiLabo(models.Model):
    """Rapport d'essai officiel (EN 001-PG019) : un rapport par fiche et par
    laboratoire, edite par le service reception a partir des resultats
    transmis. Le numero d'ordre est chronologique par annee, attribue a
    l'edition (aucun trou)."""

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("EDITE", "Édité"),
        ("SIGNE", "Signé"),
        ("REMIS", "Remis au client"),
    ]

    fiche = models.ForeignKey(FicheExecutionTravaux, on_delete=models.CASCADE, related_name="rapports")
    laboratoire = models.ForeignKey("laboratoires.Laboratoire", on_delete=models.PROTECT, related_name="rapports_essai_officiels")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")
    annee = models.PositiveIntegerField(null=True, blank=True)
    numero_ordre = models.PositiveIntegerField(null=True, blank=True)
    reference = models.CharField(max_length=150, blank=True, db_index=True)
    date_edition = models.DateField(null=True, blank=True)
    informations_diverses = models.TextField(default="R.A.S", blank=True)
    directeur_nom = models.CharField(max_length=255, blank=True, help_text="Nom & prénoms du Directeur signataire")
    date_signature = models.DateField(null=True, blank=True)
    date_remise = models.DateField(null=True, blank=True)
    edite_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("fiche", "laboratoire")
        ordering = ["-annee", "-numero_ordre", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["annee", "numero_ordre"], name="rapport_essai_numero_ordre_unique_par_annee"),
        ]
