from django.contrib.auth.models import User
from django.db import models


class Laboratoire(models.Model):
    """Referentiel des laboratoires physiques du LANEMA (Chimie, Microbiologie,
    Metrologie, ...). Dimension transverse reutilisee par qualite.Essai,
    metrologie.Equipement et facturation.DemandeAnalyse pour ventiler les KPI
    "par laboratoire"."""

    nom = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="laboratoires_diriges"
    )
    capacite_journaliere = models.PositiveIntegerField(
        default=0, help_text="Nombre d'essais/jour theorique, pour le calcul de la capacite d'utilisation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom
