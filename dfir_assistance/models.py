from django.db import models

from dfir_participants.models import EntrepriseDFIR


class MissionAssistance(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("TERMINEE", "Terminée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    entreprise = models.ForeignKey(EntrepriseDFIR, on_delete=models.CASCADE, related_name="missions_assistance")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    diagnostic_realise = models.BooleanField(default=False)
    plan_amelioration_elabore = models.BooleanField(default=False)
    satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
