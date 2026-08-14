from django.contrib.auth.models import User
from django.db import models


class DossierJuridique(models.Model):
    TYPE_CHOICES = [
        ("CONTRAT", "Contrat"),
        ("CONTENTIEUX", "Contentieux"),
        ("CONSULTATION", "Consultation"),
        ("AVIS", "Avis juridique"),
        ("DISCIPLINAIRE", "Procédure disciplinaire"),
    ]
    STATUT_CHOICES = [
        ("OUVERT", "Ouvert"),
        ("EN_COURS", "En cours"),
        ("CLOTURE", "Clôturé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_dossier = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERT")
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="dossiers_juridiques")

    class Meta:
        ordering = ["-date_ouverture"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = DossierJuridique.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"DJ-{num:04d}"
        super().save(*args, **kwargs)


class Contrat(models.Model):
    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("VALIDE", "Validé"),
        ("SIGNE", "Signé"),
        ("RENOUVELE", "Renouvelé"),
        ("EXPIRE", "Expiré"),
        ("RESILIE", "Résilié"),
    ]

    dossier = models.ForeignKey(DossierJuridique, on_delete=models.SET_NULL, null=True, blank=True, related_name="contrats")
    reference = models.CharField(max_length=50, unique=True)
    intitule = models.CharField(max_length=255)
    partie_prenante = models.CharField(max_length=255, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")
    date_redaction = models.DateField(auto_now_add=True)
    date_validation = models.DateField(null=True, blank=True)
    date_signature = models.DateField(null=True, blank=True)
    date_expiration = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_redaction"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Contrat.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"CTR-{num:04d}"
        super().save(*args, **kwargs)


class Contentieux(models.Model):
    STATUT_CHOICES = [
        ("EN_COURS", "En cours"),
        ("CLOTURE", "Clôturé"),
        ("EVITE", "Évité"),
    ]

    dossier = models.ForeignKey(DossierJuridique, on_delete=models.SET_NULL, null=True, blank=True, related_name="contentieux")
    reference = models.CharField(max_length=50, unique=True)
    partie_adverse = models.CharField(max_length=255, blank=True)
    objet = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_COURS")
    issue = models.CharField(max_length=255, blank=True, help_text="Favorable / défavorable / transaction")
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_ouverture"]
        verbose_name_plural = "Contentieux"

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Contentieux.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"CTX-{num:04d}"
        super().save(*args, **kwargs)


class AvisJuridique(models.Model):
    dossier = models.ForeignKey(DossierJuridique, on_delete=models.SET_NULL, null=True, blank=True, related_name="avis")
    demandeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="avis_demandes")
    sujet = models.CharField(max_length=255)
    date_demande = models.DateField(auto_now_add=True)
    date_reponse = models.DateField(null=True, blank=True)
    reponse = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_demande"]

    def __str__(self) -> str:  # pragma: no cover
        return self.sujet


class ProcedureDisciplinaire(models.Model):
    STATUT_CHOICES = [
        ("OUVERTE", "Ouverte"),
        ("EN_COURS", "En cours"),
        ("CLOTUREE", "Clôturée"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    agent_concerne = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="procedures_disciplinaires")
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OUVERTE")
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_ouverture"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            last = ProcedureDisciplinaire.objects.order_by("-id").first()
            num = (last.id + 1) if last else 1
            self.reference = f"PD-{num:04d}"
        super().save(*args, **kwargs)


class TexteReglementaire(models.Model):
    """Texte reglementaire (loi, decret, arrete, norme...) analyse par le
    service juridique, eventuellement rattache a un dossier."""

    STATUT_CHOICES = [
        ("APPLICABLE", "Applicable"),
        ("NON_APPLICABLE", "Non applicable"),
        ("A_SURVEILLER", "À surveiller"),
    ]

    reference = models.CharField(max_length=100, blank=True)
    intitule = models.CharField(max_length=255)
    dossier = models.ForeignKey(
        DossierJuridique, on_delete=models.SET_NULL, null=True, blank=True, related_name="textes_reglementaires"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="APPLICABLE")
    date_analyse = models.DateField(auto_now_add=True)
    synthese = models.TextField(blank=True)
    analyse_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="textes_reglementaires_analyses"
    )

    class Meta:
        ordering = ["-date_analyse"]

    def __str__(self) -> str:  # pragma: no cover
        return self.intitule
