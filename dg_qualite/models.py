from django.contrib.auth.models import User
from django.db import models


class NonConformiteQualite(models.Model):
    GRAVITE_CHOICES = [
        ("MINEURE", "Mineure"),
        ("MAJEURE", "Majeure"),
        ("CRITIQUE", "Critique"),
    ]
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("EN_TRAITEMENT", "En traitement"),
        ("CLOTUREE", "Clôturée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, default="MINEURE")
    service_concerne = models.ForeignKey(
        "core.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="non_conformites_qualite"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    date_detection = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_detection"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = NonConformiteQualite.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"NC-{num:04d}"
        super().save(*args, **kwargs)


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
        NonConformiteQualite, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions_qualite")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    date_planification = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_planification"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} - {self.description[:40]}"


class AuditQualite(models.Model):
    TYPE_CHOICES = [
        ("INTERNE", "Interne"),
        ("EXTERNE", "Externe"),
        ("ISO", "Audit ISO"),
    ]
    RESULTAT_CHOICES = [
        ("CONFORME", "Conforme"),
        ("NON_CONFORME", "Non conforme"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_audit = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INTERNE")
    organisme = models.CharField(max_length=255, blank=True)
    date_audit = models.DateField()
    resultat = models.CharField(max_length=20, choices=RESULTAT_CHOICES, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_audit"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class ReclamationClient(models.Model):
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("TRAITEE", "Traitée"),
    ]

    client_nom = models.CharField(max_length=255)
    description = models.TextField()
    date_reception = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5, apres resolution")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client_nom} - {self.date_reception}"


class RevueDirection(models.Model):
    date_revue = models.DateField()
    participants = models.TextField(blank=True)
    decisions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_revue"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Revue de direction du {self.date_revue}"


class IndicateurQualite(models.Model):
    nom = models.CharField(max_length=255)
    cible = models.DecimalField(max_digits=10, decimal_places=2)
    valeur_actuelle = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    periode = models.CharField(max_length=50, blank=True, help_text="Ex: 2026-T1")

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom

    @property
    def atteint(self) -> bool:
        return self.valeur_actuelle >= self.cible
