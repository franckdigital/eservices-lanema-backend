from django.db import models


class ClientDMCT(models.Model):
    SECTEUR_CHOICES = [
        ("COMMERCE", "Commerce"),
        ("INDUSTRIE", "Industrie"),
        ("SANTE", "Santé"),
        ("LABORATOIRE", "Laboratoire"),
        ("AUTRE", "Autre"),
    ]

    nom = models.CharField(max_length=255, unique=True)
    secteur_activite = models.CharField(max_length=20, choices=SECTEUR_CHOICES, default="AUTRE")
    contact = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class ReclamationClientDMCT(models.Model):
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("TRAITEE", "Traitée"),
    ]

    client = models.ForeignKey(ClientDMCT, on_delete=models.CASCADE, related_name="reclamations")
    description = models.TextField()
    date_reception = models.DateField(auto_now_add=True)
    date_traitement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    note_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client.nom} - {self.date_reception}"
