from django.db import models


class Vehicule(models.Model):
    STATUT_CHOICES = [
        ("DISPONIBLE", "Disponible"),
        ("EN_MISSION", "En mission"),
        ("EN_PANNE", "En panne"),
        ("EN_MAINTENANCE", "En maintenance"),
    ]

    immatriculation = models.CharField(max_length=50, unique=True)
    marque = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="DISPONIBLE")
    kilometrage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["immatriculation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.immatriculation


class PanneVehicule(models.Model):
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name="pannes")
    date_panne = models.DateField(auto_now_add=True)
    date_reparation = models.DateField(null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_panne"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Panne {self.vehicule.immatriculation} - {self.date_panne}"


class Batiment(models.Model):
    nom = models.CharField(max_length=255)
    site = models.ForeignKey(
        "core.Site", on_delete=models.SET_NULL, null=True, blank=True, related_name="batiments"
    )
    disponible = models.BooleanField(default=True)
    etat = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class Salle(models.Model):
    nom = models.CharField(max_length=255)
    capacite = models.PositiveIntegerField(default=0)
    batiment = models.ForeignKey(Batiment, on_delete=models.SET_NULL, null=True, blank=True, related_name="salles")

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class ReservationSalle(models.Model):
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE, related_name="reservations")
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    motif = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.salle.nom} - {self.date_debut}"


class InterventionTechnique(models.Model):
    batiment = models.ForeignKey(
        Batiment, on_delete=models.SET_NULL, null=True, blank=True, related_name="interventions"
    )
    type_intervention = models.CharField(max_length=100, blank=True)
    date_intervention = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_intervention"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.type_intervention} - {self.date_intervention}"
