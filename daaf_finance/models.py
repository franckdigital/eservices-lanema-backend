from django.db import models


class Budget(models.Model):
    CATEGORIE_CHOICES = [
        ("FONCTIONNEMENT", "Fonctionnement"),
        ("INVESTISSEMENT", "Investissement"),
    ]

    direction = models.ForeignKey(
        "core.Direction", on_delete=models.SET_NULL, null=True, blank=True, related_name="budgets"
    )
    annee = models.CharField(max_length=10)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default="FONCTIONNEMENT")
    montant_prevu = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    montant_engage = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    montant_realise = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    nombre_revisions = models.PositiveIntegerField(default=0)
    date_derniere_revision = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-annee"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Budget {self.annee} - {self.get_categorie_display()}"


class EcritureComptable(models.Model):
    TYPE_CHOICES = [
        ("DEBIT", "Débit"),
        ("CREDIT", "Crédit"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    date_ecriture = models.DateField()
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    piece_justificative = models.CharField(max_length=100, blank=True)
    erreur = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_ecriture"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = EcritureComptable.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"ECR-{num:05d}"
        super().save(*args, **kwargs)


class Recette(models.Model):
    STATUT_CHOICES = [
        ("EMISE", "Émise"),
        ("ENCAISSEE", "Encaissée"),
        ("IMPAYEE", "Impayée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    direction = models.ForeignKey(
        "core.Direction", on_delete=models.SET_NULL, null=True, blank=True, related_name="recettes"
    )
    type_prestation = models.CharField(max_length=255, blank=True)
    client_nom = models.CharField(max_length=255, blank=True)
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    date_emission = models.DateField()
    date_encaissement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EMISE")

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Recette.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"REC-{num:05d}"
        super().save(*args, **kwargs)


class Depense(models.Model):
    CATEGORIE_CHOICES = [
        ("FONCTIONNEMENT", "Fonctionnement"),
        ("INVESTISSEMENT", "Investissement"),
        ("MAINTENANCE", "Maintenance"),
        ("CARBURANT", "Carburant"),
        ("ELECTRICITE_EAU", "Électricité et eau"),
        ("TELECOM", "Télécommunications"),
        ("AUTRE", "Autre"),
    ]
    STATUT_CHOICES = [
        ("ENGAGEE", "Engagée"),
        ("PAYEE", "Payée"),
        ("IMPAYEE", "Impayée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    direction = models.ForeignKey(
        "core.Direction", on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses"
    )
    site = models.ForeignKey(
        "core.Site", on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses"
    )
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default="FONCTIONNEMENT")
    prestation_associee = models.CharField(max_length=255, blank=True)
    fournisseur_nom = models.CharField(max_length=255, blank=True)
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    date_engagement = models.DateField()
    date_paiement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="ENGAGEE")

    class Meta:
        ordering = ["-date_engagement"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Depense.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"DEP-{num:05d}"
        super().save(*args, **kwargs)
