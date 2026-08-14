from django.db import models


class ProjetInnovation(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("ACHEVE", "Achevé"),
        ("ABANDONNE", "Abandonné"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    titre = models.CharField(max_length=255)
    date_lancement = models.DateTimeField(auto_now_add=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    methode_developpee = models.BooleanField(default=False)
    prototype_realise = models.BooleanField(default=False)
    mis_en_oeuvre = models.BooleanField(default=False)
    partenariat = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_lancement"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre
