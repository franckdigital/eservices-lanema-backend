from django.contrib.auth.models import User
from django.db import models


class DemandeDevis(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_COURS", "En cours"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="demandes_devis",
    )
    type_analyse = models.CharField(max_length=255)
    categorie = models.CharField(max_length=255, blank=True)
    objet = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class EchantillonPrevu(models.Model):
    """Echantillon annonce par le client au moment de la demande de devis
    (nom + quantite) : liste de reference pour le service reception, qui
    cree l'echantillon reel (qualite.Echantillon, avec code de tracabilite)
    une fois le devis signe et l'echantillon physiquement receptionne."""

    demande = models.ForeignKey(DemandeDevis, on_delete=models.CASCADE, related_name="echantillons_prevus")
    nom = models.CharField(max_length=255)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.nom} x{self.quantite} ({self.demande.numero})"
