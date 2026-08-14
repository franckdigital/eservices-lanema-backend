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
