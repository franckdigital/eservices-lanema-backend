from django.db import models

from aero_maintenance.models import OrdreTravail


class IncidentTechnique(models.Model):
    GRAVITE_CHOICES = [
        ("MINEURE", "Mineure"),
        ("MAJEURE", "Majeure"),
        ("CRITIQUE", "Critique"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    ordre_travail = models.ForeignKey(
        OrdreTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents_techniques"
    )
    gravite = models.CharField(max_length=10, choices=GRAVITE_CHOICES, default="MINEURE")
    description = models.TextField()
    date_incident = models.DateField(auto_now_add=True)
    est_accident = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_incident"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class EcartReglementaire(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    date_constat = models.DateField(auto_now_add=True)
    resolu = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_constat"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class RapportSecurite(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    date_creation = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class ControleReglementaire(models.Model):
    RESULTAT_CHOICES = [
        ("REUSSI", "Réussi"),
        ("ECHEC", "Échec"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    organisme = models.CharField(max_length=100, default="ANAC")
    date_controle = models.DateField()
    resultat = models.CharField(max_length=10, choices=RESULTAT_CHOICES, default="REUSSI")

    class Meta:
        ordering = ["-date_controle"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class FormationSecurite(models.Model):
    titre = models.CharField(max_length=255)
    date_formation = models.DateField()
    nombre_participants = models.PositiveIntegerField(default=0)
    duree_heures = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    class Meta:
        ordering = ["-date_formation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre
