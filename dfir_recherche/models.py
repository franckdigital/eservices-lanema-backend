from django.db import models

from dfir_participants.models import EntrepriseDFIR


class ProjetRecherche(models.Model):
    TYPE_CHOICES = [
        ("ETUDE_TECHNIQUE", "Étude technique"),
        ("ETUDE_ENTREPRISE", "Étude pour entreprise"),
        ("RECHERCHE", "Recherche"),
    ]
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("ACHEVE", "Achevé"),
        ("ABANDONNE", "Abandonné"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    titre = models.CharField(max_length=255)
    type_projet = models.CharField(max_length=20, choices=TYPE_CHOICES, default="ETUDE_TECHNIQUE")
    entreprise = models.ForeignKey(
        EntrepriseDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="projets_recherche"
    )
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class PublicationScientifique(models.Model):
    projet = models.ForeignKey(
        ProjetRecherche, on_delete=models.SET_NULL, null=True, blank=True, related_name="publications"
    )
    titre = models.CharField(max_length=255)
    date_publication = models.DateField()

    class Meta:
        ordering = ["-date_publication"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class RapportRecherche(models.Model):
    projet = models.ForeignKey(ProjetRecherche, on_delete=models.CASCADE, related_name="rapports")
    titre = models.CharField(max_length=255)
    date_creation = models.DateField(auto_now_add=True)
    valide = models.BooleanField(default=False)
    date_validation = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class RecommandationRecherche(models.Model):
    rapport = models.ForeignKey(RapportRecherche, on_delete=models.CASCADE, related_name="recommandations")
    description = models.TextField()
    appliquee = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Recommandation - {self.rapport.titre}"


class CollaborationRecherche(models.Model):
    TYPE_CHOICES = [
        ("UNIVERSITE", "Université"),
        ("CENTRE_RECHERCHE", "Centre de recherche"),
        ("AUTRE", "Autre"),
    ]

    nom_partenaire = models.CharField(max_length=255)
    type_partenaire = models.CharField(max_length=20, choices=TYPE_CHOICES, default="UNIVERSITE")
    date_debut = models.DateField()

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom_partenaire
