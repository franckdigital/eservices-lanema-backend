from django.db import models


class PieceRechange(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100, blank=True)
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=0)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    est_critique = models.BooleanField(default=False)

    class Meta:
        ordering = ["designation"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.reference} - {self.designation}"


class MouvementPieceRechange(models.Model):
    TYPE_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
    ]

    piece = models.ForeignKey(PieceRechange, on_delete=models.CASCADE, related_name="mouvements")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.piece.reference} - {self.type_mouvement} ({self.quantite})"
