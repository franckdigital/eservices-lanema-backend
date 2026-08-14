from django.contrib.auth.models import User
from django.db import models


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    contact = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class DemandeAchat(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("TRAITEE", "Traitée"),
        ("REJETEE", "Rejetée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    direction = models.ForeignKey(
        "core.Direction", on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_achat"
    )
    objet = models.CharField(max_length=255)
    demandeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_achat")
    date_demande = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = DemandeAchat.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"DA-{num:05d}"
        super().save(*args, **kwargs)


class BonCommande(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("LIVRE", "Livré"),
        ("EN_RETARD", "En retard"),
        ("ANNULE", "Annulé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    demande = models.ForeignKey(DemandeAchat, on_delete=models.SET_NULL, null=True, blank=True, related_name="bons_commande")
    fournisseur_nom = models.CharField(max_length=255, blank=True)
    montant = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    date_commande = models.DateField(auto_now_add=True)
    date_livraison_prevue = models.DateField(null=True, blank=True)
    date_livraison_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    conforme = models.BooleanField(null=True, blank=True)
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")

    class Meta:
        ordering = ["-date_commande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = BonCommande.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"BC-{num:05d}"
        super().save(*args, **kwargs)


class Marche(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("ATTRIBUE", "Attribué"),
        ("EXECUTE", "Exécuté"),
        ("ANNULE", "Annulé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    objet = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date_attribution = models.DateField(null=True, blank=True)
    respect_plan = models.BooleanField(default=True, help_text="Conforme au plan de passation des marchés")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")

    class Meta:
        ordering = ["-date_attribution"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference
