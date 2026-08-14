from django.contrib.auth.models import User
from django.db import models


class Bien(models.Model):
    CATEGORIE_CHOICES = [
        ("MOBILIER", "Mobilier"),
        ("INFORMATIQUE", "Informatique"),
        ("VEHICULE", "Véhicule"),
        ("IMMOBILIER", "Immobilier"),
        ("EQUIPEMENT", "Équipement technique"),
        ("AUTRE", "Autre"),
    ]
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("EN_MAINTENANCE", "En maintenance"),
        ("REFORME", "Réformé"),
        ("PERDU", "Perdu"),
        ("SORTI", "Sorti"),
    ]

    code = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default="AUTRE")
    date_acquisition = models.DateField(null=True, blank=True)
    valeur_acquisition = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valeur_actuelle = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    duree_amortissement_ans = models.PositiveIntegerField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")
    localisation = models.CharField(max_length=255, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="biens_patrimoine")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} - {self.designation}"


class MouvementBien(models.Model):
    TYPE_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
        ("TRANSFERT", "Transfert"),
        ("REFORME", "Réforme"),
        ("PERTE", "Perte"),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="mouvements")
    type_mouvement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    motif = models.TextField(blank=True)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    effectue_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="mouvements_bien")

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_mouvement_display()} - {self.bien.code}"


class MaintenanceBien(models.Model):
    TYPE_CHOICES = [
        ("PREVENTIVE", "Préventive"),
        ("CORRECTIVE", "Corrective"),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="maintenances")
    type_maintenance = models.CharField(max_length=20, choices=TYPE_CHOICES, default="PREVENTIVE")
    date_maintenance = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_maintenance"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Maintenance {self.bien.code} - {self.date_maintenance}"


class InventairePatrimoine(models.Model):
    date_inventaire = models.DateField()
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventaires_patrimoine")
    nombre_biens_verifies = models.PositiveIntegerField(default=0)
    ecarts_constates = models.PositiveIntegerField(default=0)
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_inventaire"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Inventaire du {self.date_inventaire}"
