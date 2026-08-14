from django.db import models


class ClientAeronautique(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    contact = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class Aeronef(models.Model):
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_MAINTENANCE", "En maintenance"),
        ("HORS_SERVICE", "Hors service"),
    ]

    immatriculation = models.CharField(max_length=50, unique=True)
    type_aeronef = models.CharField(max_length=255, blank=True)
    client = models.ForeignKey(
        ClientAeronautique, on_delete=models.SET_NULL, null=True, blank=True, related_name="aeronefs"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")

    class Meta:
        ordering = ["immatriculation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.immatriculation


class ReclamationClientDAE(models.Model):
    """Reclamation d'un client de la Direction de l'Aeronautique (distincte de
    clients.ReclamationClient et dg_qualite.ReclamationClient, memes principes
    de separation par domaine deja etablis)."""

    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("TRAITEE", "Traitée"),
    ]

    client = models.ForeignKey(ClientAeronautique, on_delete=models.CASCADE, related_name="reclamations")
    description = models.TextField()
    date_reception = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client.nom} - {self.date_reception}"
