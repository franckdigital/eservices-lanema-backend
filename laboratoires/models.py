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
    # Rattachement hierarchique, repris dans la reference des rapports d'essai
    # (000/AN/Direction/Sous-Direction//Labo) et le N° de fiche d'execution des travaux.
    direction = models.CharField(max_length=20, blank=True, help_text="Code de la direction (ex. DEA)")
    sous_direction = models.CharField(max_length=20, blank=True, help_text="Code de la sous-direction (ex. SDCPA)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom
