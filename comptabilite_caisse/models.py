from django.conf import settings
from django.db import models


class Caisse(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="caisses"
    )
    solde_initial = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class MouvementCaisse(models.Model):
    TYPE_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
    ]

    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE, related_name="mouvements")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    motif = models.CharField(max_length=255, blank=True)
    justificatif = models.FileField(upload_to="comptabilite/caisse/", null=True, blank=True)

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.caisse.nom} - {self.type_mouvement} {self.montant}"
