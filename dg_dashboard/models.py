from django.db import models


class ObjectifStrategique(models.Model):
    """Suivi manuel des objectifs qui n'ont pas de source de donnees automatique
    ailleurs dans l'application (objectif strategique libre, execution
    budgetaire, digitalisation des processus)."""

    TYPE_CHOICES = [
        ("OBJECTIF", "Objectif stratégique"),
        ("BUDGET", "Exécution budgétaire"),
        ("DIGITALISATION", "Digitalisation des processus"),
    ]
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("ATTEINT", "Atteint"),
        ("NON_ATTEINT", "Non atteint"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="OBJECTIF")
    nom = models.CharField(max_length=255)
    direction = models.ForeignKey(
        "core.Direction", on_delete=models.SET_NULL, null=True, blank=True, related_name="objectifs_strategiques"
    )
    service = models.ForeignKey(
        "core.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="objectifs_strategiques"
    )
    cible = models.DecimalField(max_digits=14, decimal_places=2, help_text="Valeur cible (montant, %, nombre...)")
    valeur_actuelle = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    periode = models.CharField(max_length=50, blank=True, help_text="Ex: 2026, 2026-T1")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} - {self.nom}"

    @property
    def taux_realisation(self):
        if not self.cible:
            return None
        return round(float(self.valeur_actuelle) / float(self.cible) * 100, 1)
