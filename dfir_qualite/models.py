from django.db import models

from dfir_formations.models import Formation
from dfir_participants.models import EntrepriseDFIR, ParticipantDFIR


class ReclamationDFIR(models.Model):
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("TRAITEE", "Traitée"),
    ]

    entreprise = models.ForeignKey(
        EntrepriseDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="reclamations_dfir"
    )
    participant = models.ForeignKey(
        ParticipantDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="reclamations_dfir"
    )
    description = models.TextField()
    date_reception = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Reclamation - {self.date_reception}"


class AmeliorationProgramme(models.Model):
    formation = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="ameliorations"
    )
    description = models.TextField()
    date_mise_en_oeuvre = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_mise_en_oeuvre"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Amelioration - {self.formation}"


class AuditDFIR(models.Model):
    RESULTAT_CHOICES = [
        ("CONFORME", "Conforme"),
        ("NON_CONFORME", "Non conforme"),
        ("CONFORME_AVEC_RESERVES", "Conforme avec réserves"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_audit = models.CharField(max_length=100, blank=True)
    date_audit = models.DateField()
    resultat = models.CharField(max_length=25, choices=RESULTAT_CHOICES, default="CONFORME")

    class Meta:
        ordering = ["-date_audit"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
