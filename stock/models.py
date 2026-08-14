from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.utils import timezone


class Entrepot(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    adresse = models.TextField(blank=True)

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.nom


class Emplacement(models.Model):
    code = models.CharField(max_length=100, unique=True)
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name="emplacements")
    allee = models.CharField(max_length=50, blank=True)
    rayon = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class Domaine(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class CategorieArticle(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    domaine = models.ForeignKey(
        Domaine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories",
    )

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class Article(models.Model):
    reference_interne = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    categorie = models.ForeignKey(
        CategorieArticle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    emplacement = models.ForeignKey(
        'Emplacement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    unite_mesure = models.CharField(max_length=50, default="UNITE")
    quantite_stock = models.FloatField(default=0)
    seuil_alerte = models.FloatField(default=0)
    est_critique = models.BooleanField(default=False)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.reference_interne} - {self.designation}"


class Lot(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="lots")
    numero_lot = models.CharField(max_length=100)
    quantite_attendue = models.FloatField(default=0)  # Quantité commandée/attendue
    quantite_initiale = models.FloatField(default=0)  # Quantité effectivement reçue
    quantite_restante = models.FloatField(default=0)
    unite = models.CharField(max_length=50, default="UNITE")
    date_peremption = models.DateField(null=True, blank=True)
    ouvert = models.BooleanField(default=False)
    emplacement = models.ForeignKey(
        'Emplacement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lots",
    )

    class Meta:
        unique_together = ("article", "numero_lot")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.article.reference_interne} - {self.numero_lot}"


class Alerte(models.Model):
    TYPE_CHOICES = [
        ("STOCK_CRITIQUE", "Stock critique"),
        ("RUPTURE", "Rupture"),
        ("PEREMPTION", "Péremption"),
        ("QUARANTAINE", "Quarantaine"),
    ]
    NIVEAU_CHOICES = [
        ("CRITIQUE", "Critique"),
        ("URGENT", "Urgent"),
        ("AVERTISSEMENT", "Avertissement"),
    ]

    titre = models.CharField(max_length=255)
    message = models.TextField()
    type_alerte = models.CharField(max_length=50, choices=TYPE_CHOICES)
    niveau_priorite = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    date_creation = models.DateTimeField(auto_now_add=True)
    traitee = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertes_traitees",
    )

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class Quarantaine(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="quarantaines")
    motif = models.TextField()
    date_mise_en_quarantaine = models.DateTimeField(auto_now_add=True)
    mis_en_quarantaine_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quarantaines_creees",
    )
    levee = models.BooleanField(default=False)
    date_levee = models.DateTimeField(null=True, blank=True)
    leve_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quarantaines_levees",
    )
    decision = models.CharField(max_length=100, blank=True)
    commentaire = models.TextField(blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Quarantaine {self.lot.numero_lot}"


class Reception(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("VERIFIEE", "Vérifiée"),
        ("VALIDEE", "Validée"),
        ("REJETEE", "Rejetée"),
    ]
    
    numero_reception = models.CharField(max_length=100, unique=True)
    fournisseur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receptions_fournisseur",
        limit_choices_to={"client_profile__role": "FOURNISSEUR"},
    )
    date_reception = models.DateField(auto_now_add=True)
    date_livraison_prevue = models.DateField(null=True, blank=True)
    numero_commande = models.CharField(max_length=100, blank=True)
    numero_bl = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    observations = models.TextField(blank=True)
    receptionne_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receptions_effectuees",
    )
    verifie_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receptions_verifiees",
    )
    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receptions_validees",
    )
    date_verification = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_reception
    
    @property
    def conforme(self):
        """Retourne True si toutes les lignes sont conformes"""
        if not self.lignes.exists():
            return True
        return not self.lignes.filter(conforme=False).exists()
    
    def save(self, *args, **kwargs):
        if not self.numero_reception:
            # Auto-générer le numéro de réception
            from django.utils import timezone
            year = timezone.now().year
            last = Reception.objects.filter(
                numero_reception__startswith=f"REC-{year}-"
            ).order_by("-numero_reception").first()
            if last:
                try:
                    last_num = int(last.numero_reception.split("-")[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.numero_reception = f"REC-{year}-{new_num:03d}"
        super().save(*args, **kwargs)


class LigneReception(models.Model):
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, null=True, blank=True)
    quantite_attendue = models.FloatField(default=0)
    quantite_recue = models.FloatField(default=0)
    unite = models.CharField(max_length=50, blank=True)
    numero_lot = models.CharField(max_length=100, blank=True)
    date_fabrication = models.DateField(null=True, blank=True)
    date_peremption = models.DateField(null=True, blank=True)
    conforme = models.BooleanField(default=True)
    observations = models.TextField(blank=True)


class TransfertInterne(models.Model):
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="transferts")
    emplacement_source = models.ForeignKey(
        Emplacement,
        on_delete=models.CASCADE,
        related_name="transferts_source",
        null=True,
        blank=True,
    )
    emplacement_destination = models.ForeignKey(
        Emplacement,
        on_delete=models.CASCADE,
        related_name="transferts_destination",
    )
    quantite = models.FloatField(default=0)
    unite = models.CharField(max_length=50, default="UNITE")
    motif = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    valide = models.BooleanField(default=False)
    execute = models.BooleanField(default=False)


class SortieStock(models.Model):
    """Modèle pour les sorties de stock (consommation, utilisation)"""
    TYPE_SORTIE_CHOICES = [
        ("CONSOMMATION", "Consommation laboratoire"),
        ("ANALYSE", "Utilisation pour analyse"),
        ("PERTE", "Perte/Casse"),
        ("PEREMPTION", "Péremption"),
        ("RETOUR_FOURNISSEUR", "Retour fournisseur"),
        ("DESTRUCTION", "Destruction"),
        ("AUTRE", "Autre"),
    ]
    
    numero_sortie = models.CharField(max_length=100, unique=True)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="sorties")
    quantite = models.FloatField()
    type_sortie = models.CharField(max_length=50, choices=TYPE_SORTIE_CHOICES)
    motif = models.TextField(blank=True)
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sorties_stock",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sorties_stock",
    )
    date_sortie = models.DateTimeField(auto_now_add=True)
    valide = models.BooleanField(default=False)
    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sorties_validees",
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_sortie"]
    
    def __str__(self) -> str:
        return f"{self.numero_sortie} - {self.lot.article.designation}"
    
    def save(self, *args, **kwargs):
        if not self.numero_sortie:
            last_sortie = SortieStock.objects.order_by('-id').first()
            next_id = (last_sortie.id + 1) if last_sortie else 1
            self.numero_sortie = f"SOR-{timezone.now().year}-{next_id:05d}"
        super().save(*args, **kwargs)


class MouvementStock(models.Model):
    """Modèle pour la traçabilité complète de tous les mouvements de stock"""
    TYPE_MOUVEMENT_CHOICES = [
        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
        ("TRANSFERT", "Transfert"),
        ("AJUSTEMENT", "Ajustement inventaire"),
        ("QUARANTAINE_ENTREE", "Mise en quarantaine"),
        ("QUARANTAINE_SORTIE", "Sortie de quarantaine"),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="mouvements")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="mouvements", null=True, blank=True)
    type_mouvement = models.CharField(max_length=50, choices=TYPE_MOUVEMENT_CHOICES)
    quantite = models.FloatField()
    quantite_avant = models.FloatField(default=0)
    quantite_apres = models.FloatField(default=0)
    reference_document = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    reception = models.ForeignKey(Reception, on_delete=models.SET_NULL, null=True, blank=True, related_name="mouvements")
    sortie = models.ForeignKey(SortieStock, on_delete=models.SET_NULL, null=True, blank=True, related_name="mouvements")
    transfert = models.ForeignKey(TransfertInterne, on_delete=models.SET_NULL, null=True, blank=True, related_name="mouvements")
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mouvements_stock",
    )
    date_mouvement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-date_mouvement"]
    
    def __str__(self) -> str:
        return f"{self.type_mouvement} - {self.article.designation} ({self.quantite})"


class Inventaire(models.Model):
    """Modèle pour la gestion des inventaires physiques"""
    TYPE_INVENTAIRE_CHOICES = [
        ("COMPLET", "Inventaire complet"),
        ("PARTIEL", "Inventaire partiel"),
        ("TOURNANT", "Inventaire tournant"),
        ("ANNUEL", "Inventaire annuel"),
    ]
    STATUT_CHOICES = [
        ("PLANIFIE", "Planifié"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("VALIDE", "Validé"),
        ("ANNULE", "Annulé"),
    ]
    
    numero_inventaire = models.CharField(max_length=100, unique=True)
    type_inventaire = models.CharField(max_length=50, choices=TYPE_INVENTAIRE_CHOICES, default="COMPLET")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIE")
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name="inventaires", null=True, blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventaires_responsable",
    )
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-date_debut"]
    
    def __str__(self) -> str:
        return f"{self.numero_inventaire} - {self.get_type_inventaire_display()}"
    
    def save(self, *args, **kwargs):
        if not self.numero_inventaire:
            last = Inventaire.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.numero_inventaire = f"INV-{timezone.now().year}-{next_id:05d}"
        super().save(*args, **kwargs)


class LigneInventaire(models.Model):
    """Ligne d'inventaire pour chaque article/lot compté"""
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="lignes_inventaire")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="lignes_inventaire", null=True, blank=True)
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True)
    quantite_theorique = models.FloatField(default=0)
    quantite_comptee = models.FloatField(null=True, blank=True)
    ecart = models.FloatField(default=0)
    commentaire = models.TextField(blank=True)
    compte_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lignes_inventaire_comptees",
    )
    date_comptage = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["article__designation"]
    
    def save(self, *args, **kwargs):
        if self.quantite_comptee is not None:
            self.ecart = self.quantite_comptee - self.quantite_theorique
        super().save(*args, **kwargs)
