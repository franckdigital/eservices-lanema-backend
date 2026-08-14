import uuid

from django.db import models

from dfir_formateurs.models import FormateurDFIR
from dfir_participants.models import EntrepriseDFIR, ParticipantDFIR


class Formation(models.Model):
    TYPE_CHOICES = [
        ("INTER_ENTREPRISE", "Inter-entreprises"),
        ("INTRA_ENTREPRISE", "Intra-entreprise"),
        ("SUR_MESURE", "Sur mesure"),
    ]
    MODALITE_CHOICES = [
        ("PRESENTIEL", "Présentiel"),
        ("EN_LIGNE", "En ligne"),
        ("HYBRIDE", "Hybride"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    titre = models.CharField(max_length=255)
    type_formation = models.CharField(max_length=20, choices=TYPE_CHOICES, default="INTER_ENTREPRISE")
    modalite = models.CharField(max_length=15, choices=MODALITE_CHOICES, default="PRESENTIEL")
    certifiante = models.BooleanField(default=False)
    duree_heures = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["titre"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre


class SessionFormation(models.Model):
    STATUT_CHOICES = [
        ("PLANIFIEE", "Planifiée"),
        ("EN_COURS", "En cours"),
        ("TERMINEE", "Terminée"),
        ("ANNULEE", "Annulée"),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="sessions")
    formateur = models.ForeignKey(
        FormateurDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    entreprise = models.ForeignKey(
        EntrepriseDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions_formation"
    )
    date_debut = models.DateTimeField()
    date_fin_prevue = models.DateTimeField(null=True, blank=True)
    date_fin_reelle = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIEE")
    capacite_max = models.PositiveIntegerField(default=0)
    evaluation_formateur = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    evaluation_session = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Satisfaction sur 5")
    cout_revient = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.formation.titre} - {self.date_debut}"


class InscriptionParticipant(models.Model):
    session = models.ForeignKey(SessionFormation, on_delete=models.CASCADE, related_name="inscriptions")
    participant = models.ForeignKey(ParticipantDFIR, on_delete=models.CASCADE, related_name="inscriptions")
    present = models.BooleanField(null=True, blank=True)
    reussite = models.BooleanField(null=True, blank=True)
    certifie = models.BooleanField(default=False)
    abandon = models.BooleanField(default=False)

    # Fiche de satisfaction : lien public unique envoyé au participant (aucun
    # compte requis) pour évaluer la formation et le formateur après la session.
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    note_formateur = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    note_session = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Note sur 5")
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.participant} - {self.session}"


class SupportPedagogique(models.Model):
    TYPE_CHOICES = [
        ("DOCUMENT", "Document"),
        ("VIDEO", "Vidéo"),
        ("QUIZ", "Quiz"),
        ("AUTRE", "Autre"),
    ]

    formation = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="supports"
    )
    titre = models.CharField(max_length=255)
    type_contenu = models.CharField(max_length=20, choices=TYPE_CHOICES, default="DOCUMENT")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_maj = models.DateTimeField(null=True, blank=True)
    nombre_telechargements = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.titre
