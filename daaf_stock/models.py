from django.db import models


class ArticleStock(models.Model):
    reference = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100, blank=True)
    unite = models.CharField(max_length=50, default="UNITE")
    quantite_stock = models.FloatField(default=0)
    seuil_alerte = models.FloatField(default=0)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["designation"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.reference} - {self.designation}"


class LotStock(models.Model):
    article = models.ForeignKey(ArticleStock, on_delete=models.CASCADE, related_name="lots")
    numero_lot = models.CharField(max_length=100, blank=True)
    quantite = models.FloatField(default=0)
    date_peremption = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["date_peremption"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.article.reference} - {self.numero_lot}"


class MouvementStockAdmin(models.Model):
    TYPE_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
    ]

    article = models.ForeignKey(ArticleStock, on_delete=models.CASCADE, related_name="mouvements")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.FloatField(default=0)
    date_mouvement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.type} - {self.article.reference} ({self.quantite})"
