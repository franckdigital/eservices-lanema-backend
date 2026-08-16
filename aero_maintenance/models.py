from django.conf import settings
from django.db import models
from django.utils import timezone

from aero_clients.models import Aeronef
from aero_stock.models import PieceRechange


class OrdreTravail(models.Model):
    TYPE_CHOICES = [
        ("PREVENTIVE", "Maintenance préventive"),
        ("CORRECTIVE", "Maintenance corrective"),
        ("URGENCE", "Urgence"),
    ]
    # Cycle de vie complet cf. cahier des charges DAE (section 11) : de la
    # planification a la cloture administrative, avec un palier "Controle
    # qualite" obligatoire avant de pouvoir passer a "Termine" (verrou —
    # cf. OrdreTravailViewSet.changer_statut / TRANSITIONS_OT).
    STATUT_CHOICES = [
        ("A_PLANIFIER", "À planifier"),
        ("PLANIFIE", "Planifié"),
        ("EN_COURS", "En cours"),
        ("EN_ATTENTE_PIECE", "En attente pièce"),
        ("EN_ATTENTE_CLIENT", "En attente client"),
        ("CONTROLE_QUALITE", "Contrôle qualité"),
        ("TERMINE", "Terminé"),
        ("VALIDE", "Validé"),
        ("CLOTURE", "Clôturé"),
        ("ANNULE", "Annulé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    aeronef = models.ForeignKey(Aeronef, on_delete=models.CASCADE, related_name="ordres_travail")
    type_intervention = models.CharField(max_length=20, choices=TYPE_CHOICES, default="CORRECTIVE")
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordres_travail_dae"
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_prise_charge = models.DateTimeField(null=True, blank=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="A_PLANIFIER")
    piece_utilisee = models.ForeignKey(
        PieceRechange, on_delete=models.SET_NULL, null=True, blank=True, related_name="ordres_travail"
    )

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class CertificatDAE(models.Model):
    """Certificat de fin d'intervention, numerote independamment de la
    reference de l'OT — cf. cahier des charges DAE section 19 : numerotation
    dediee CERT-DAE-AAAA-NNNNN. Un seul certificat par OT, cree a la premiere
    generation (cf. OrdreTravailViewSet.telecharger_certificat) puis reutilise
    a chaque telechargement suivant, pour que le numero reste stable."""

    ordre_travail = models.OneToOneField(
        "OrdreTravail", on_delete=models.CASCADE, related_name="certificat"
    )
    numero = models.CharField(max_length=50, unique=True, blank=True)
    date_emission = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero

    def save(self, *args, **kwargs):
        if not self.numero:
            year = timezone.now().year
            last = CertificatDAE.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.numero = f"CERT-DAE-{year}-{num:05d}"
        super().save(*args, **kwargs)


class InterventionTechnique(models.Model):
    """Journal d'intervention technique sur un OT — un technicien peut
    ajouter plusieurs entrees au fil du travail (diagnostic, demontage,
    reparation...), chacune avec temps passe, mesures et resultat. Cf.
    cahier des charges section 13 : ce sont ces donnees reelles qui
    permettent ensuite de calculer automatiquement les KPI (temps moyen,
    productivite...) plutot que de les faire saisir manuellement."""

    OPERATION_CHOICES = [
        ("DIAGNOSTIC", "Diagnostic"),
        ("DEMONTAGE", "Démontage"),
        ("INSPECTION", "Inspection"),
        ("NETTOYAGE", "Nettoyage"),
        ("REPARATION", "Réparation"),
        ("REMONTAGE", "Remontage"),
        ("TEST", "Test"),
        ("CONTROLE", "Contrôle"),
        ("AUTRE", "Autre"),
    ]

    ordre_travail = models.ForeignKey(OrdreTravail, on_delete=models.CASCADE, related_name="interventions")
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="interventions_dae"
    )
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES, default="AUTRE")
    description = models.TextField(blank=True, help_text="Opérations réalisées")
    temps_passe_minutes = models.PositiveIntegerField(default=0)
    mesures = models.TextField(blank=True)
    resultat = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    pieces_utilisees = models.ManyToManyField(PieceRechange, blank=True, related_name="interventions_dae")
    date_intervention = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_intervention"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.ordre_travail.reference} - {self.get_operation_display()}"


class EquipementAeronautique(models.Model):
    """Cf. cahier des charges DAE section 7 : equipements aeronautiques
    generiques (electrique, hydraulique, mecanique, autre) — les roues et
    batteries, deja modelisees en detail (sections 8-9, cf. RoueAeronef /
    BatterieAeronef ci-dessous), ne sont pas dupliquees ici pour eviter deux
    sources de verite sur le meme equipement."""

    TYPE_CHOICES = [
        ("ELECTRIQUE", "Équipement électrique"),
        ("HYDRAULIQUE", "Équipement hydraulique"),
        ("MECANIQUE", "Équipement mécanique"),
        ("AUTRE", "Autre équipement aéronautique"),
    ]
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_CONTROLE", "En contrôle"),
        ("REPARE", "Réparé"),
        ("REMPLACE", "Remplacé"),
        ("NON_CONFORME", "Non conforme"),
    ]

    reference = models.CharField(max_length=50, blank=True)
    numero_serie = models.CharField(max_length=50, unique=True)
    type_equipement = models.CharField(max_length=15, choices=TYPE_CHOICES, default="AUTRE")
    fabricant = models.CharField(max_length=255, blank=True)
    modele = models.CharField(max_length=255, blank=True)
    proprietaire = models.CharField(max_length=255, blank=True, help_text="Si différent de l'exploitant (client)")
    aeronef = models.ForeignKey(
        Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipements_aeronautiques"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    date_reception = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["numero_serie"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_serie


class RoueAeronef(models.Model):
    """Cf. cahier des charges DAE section 8 : donnees techniques + cycle de
    vie complet (reception -> identification -> demontage -> inspection ->
    ... -> validation), ce dernier trace via le journal InspectionRoue
    ci-dessous plutot que par un simple champ statut a plat."""

    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_INSPECTION", "En inspection"),
        ("REPAREE", "Réparée"),
        ("REMPLACEE", "Remplacée"),
        ("NON_CONFORME", "Non conforme"),
    ]

    reference = models.CharField(max_length=50, blank=True)
    numero_serie = models.CharField(max_length=50, unique=True)
    constructeur = models.CharField(max_length=255, blank=True)
    type_roue = models.CharField(max_length=100, blank=True)
    aeronef = models.ForeignKey(Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="roues")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    nombre_cycles = models.PositiveIntegerField(default=0)
    date_derniere_intervention = models.DateField(null=True, blank=True)
    prochaine_inspection = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["numero_serie"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_serie


class InspectionRoue(models.Model):
    """Journal des etapes du cycle de traitement d'une roue — cf. cahier des
    charges section 8 : reception, identification, demontage, inspection,
    nettoyage, reparation, remplacement de composants, remontage,
    equilibrage, controle final, validation. Chaque entree fait avancer
    RoueAeronef.statut (cf. RoueAeronefViewSet.perform_create ou
    InspectionRoueViewSet.perform_create — meme principe que
    InterventionTechnique pour les OT)."""

    TYPE_CHOICES = [
        ("RECEPTION", "Réception"),
        ("IDENTIFICATION", "Identification"),
        ("DEMONTAGE", "Démontage"),
        ("INSPECTION_PERIODIQUE", "Inspection périodique"),
        ("NETTOYAGE", "Nettoyage"),
        ("REPARATION", "Réparation"),
        ("REMPLACEMENT_COMPOSANT", "Remplacement de composants"),
        ("REMONTAGE", "Remontage"),
        ("EQUILIBRAGE", "Équilibrage"),
        ("CONTROLE_FINAL", "Contrôle final"),
        ("VALIDATION", "Validation"),
    ]

    roue = models.ForeignKey(RoueAeronef, on_delete=models.CASCADE, related_name="inspections")
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections_roues"
    )
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    date_inspection = models.DateField(auto_now_add=True)
    conforme = models.BooleanField(default=True)
    type_inspection = models.CharField(max_length=25, choices=TYPE_CHOICES, default="INSPECTION_PERIODIQUE")
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_inspection"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.roue.numero_serie} - {self.date_inspection}"


class BatterieAeronef(models.Model):
    """Cf. cahier des charges DAE section 9 : donnees de reception + tests
    dont le resultat (CONFORME / NON CONFORME / A REPARER / A REMPLACER) est
    trace via le journal TestBatterie ci-dessous."""

    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_TEST", "En test"),
        ("RECHARGEE", "Rechargée"),
        ("REPAREE", "Réparée"),
        ("REMPLACEE", "Remplacée"),
        ("HORS_SERVICE", "Hors service"),
    ]

    reference = models.CharField(max_length=50, blank=True)
    numero_serie = models.CharField(max_length=50, unique=True)
    type_batterie = models.CharField(max_length=100, blank=True)
    capacite_nominale = models.CharField(max_length=50, blank=True, help_text="Ex. 30 Ah")
    tension_nominale = models.CharField(max_length=50, blank=True, help_text="Ex. 24 V")
    aeronef = models.ForeignKey(Aeronef, on_delete=models.SET_NULL, null=True, blank=True, related_name="batteries")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    date_mise_en_service = models.DateField(null=True, blank=True)
    date_derniere_maintenance = models.DateField(null=True, blank=True)
    prochain_controle = models.DateField(null=True, blank=True, help_text="Échéance du prochain contrôle/test")

    class Meta:
        ordering = ["numero_serie"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_serie


class TestBatterie(models.Model):
    """Journal des tests batterie — cf. cahier des charges section 9 :
    tension, capacité, état, température, charge, décharge, puis une
    décision qui fait évoluer BatterieAeronef.statut (cf.
    TestBatterieViewSet.perform_create)."""

    RESULTAT_CHOICES = [
        ("CONFORME", "Conforme"),
        ("NON_CONFORME", "Non conforme"),
        ("A_REPARER", "À réparer"),
        ("A_REMPLACER", "À remplacer"),
    ]

    batterie = models.ForeignKey(BatterieAeronef, on_delete=models.CASCADE, related_name="tests")
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="tests_batteries"
    )
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    date_test = models.DateTimeField(auto_now_add=True)
    tension_mesuree = models.CharField(max_length=50, blank=True)
    capacite_mesuree = models.CharField(max_length=50, blank=True)
    etat = models.CharField(max_length=100, blank=True)
    temperature = models.CharField(max_length=50, blank=True)
    charge = models.BooleanField(default=False, help_text="Test de charge effectué")
    decharge = models.BooleanField(default=False, help_text="Test de décharge effectué")
    resultat = models.CharField(max_length=15, choices=RESULTAT_CHOICES, default="CONFORME")
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_test"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.batterie.numero_serie} - {self.date_test:%Y-%m-%d}"
