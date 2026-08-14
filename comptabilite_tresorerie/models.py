from django.db import models


class CompteBancaire(models.Model):
    nom_banque = models.CharField(max_length=255)
    numero_compte = models.CharField(max_length=100, unique=True)
    intitule = models.CharField(max_length=255, blank=True)
    solde_initial = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom_banque"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.nom_banque} - {self.numero_compte}"


class MouvementBancaire(models.Model):
    TYPE_CHOICES = [
        ("CREDIT", "Crédit"),
        ("DEBIT", "Débit"),
    ]

    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name="mouvements")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date_mouvement = models.DateField()
    libelle = models.CharField(max_length=255, blank=True)
    rapproche = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.compte.numero_compte} - {self.type_mouvement} {self.montant}"


class RapprochementBancaire(models.Model):
    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name="rapprochements")
    date_rapprochement = models.DateField(auto_now_add=True)
    solde_releve = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    solde_comptable = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    ecart = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    valide = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_rapprochement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Rapprochement {self.compte.numero_compte} - {self.date_rapprochement}"
