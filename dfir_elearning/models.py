import uuid

from django.db import models

from dfir_formations.models import Formation, SessionFormation
from dfir_participants.models import ParticipantDFIR


class Lecon(models.Model):
    """Une leçon e-learning rattachée à une formation du catalogue. Un
    participant y accède dès lors qu'il est inscrit (InscriptionParticipant,
    hors abandon) à une session de cette formation."""

    TYPE_CHOICES = [
        ("VIDEO", "Vidéo"),
        ("DOCUMENT", "Document"),
        ("TEXTE", "Texte"),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="lecons")
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type_contenu = models.CharField(max_length=10, choices=TYPE_CHOICES, default="VIDEO")
    url_contenu = models.URLField(blank=True, help_text="Lien vidéo, document ou ressource externe")
    texte_contenu = models.TextField(blank=True, help_text="Contenu texte si type = TEXTE")
    ordre = models.PositiveIntegerField(default=0)
    duree_minutes = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["formation_id", "ordre", "id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.formation.titre} - {self.titre}"


class ClasseVirtuelle(models.Model):
    """Classe virtuelle (visioconférence) rattachée à une session de
    formation — un lien externe (Google Meet, Teams...), pas d'intégration
    API : le formateur/l'encadrement colle simplement le lien de la réunion."""

    PROVIDER_CHOICES = [
        ("GOOGLE_MEET", "Google Meet"),
        ("TEAMS", "Microsoft Teams"),
        ("ZOOM", "Zoom"),
        ("AUTRE", "Autre"),
    ]

    session = models.ForeignKey(SessionFormation, on_delete=models.CASCADE, related_name="classes_virtuelles")
    titre = models.CharField(max_length=255)
    provider = models.CharField(max_length=15, choices=PROVIDER_CHOICES, default="GOOGLE_MEET")
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    join_url = models.URLField()
    compte_rendu = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_debut"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.titre} - {self.date_debut}"


class ProgressionLecon(models.Model):
    """Suivi personnel d'un participant sur une leçon : vue ou non, note
    personnelle libre (ses propres annotations, pas une évaluation)."""

    participant = models.ForeignKey(ParticipantDFIR, on_delete=models.CASCADE, related_name="progressions")
    lecon = models.ForeignKey(Lecon, on_delete=models.CASCADE, related_name="progressions")
    vu = models.BooleanField(default=False)
    date_vu = models.DateTimeField(null=True, blank=True)
    note_personnelle = models.TextField(blank=True)

    class Meta:
        unique_together = ("participant", "lecon")
        ordering = ["-id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.participant} - {self.lecon}"


class CertificatFormation(models.Model):
    """Certificat délivré à un participant pour une inscription (session)
    donnée — généralement après réussite. Le PDF est généré à la demande
    (non stocké), la vérification publique se fait via `code_verification`."""

    inscription = models.OneToOneField(
        "dfir_formations.InscriptionParticipant", on_delete=models.CASCADE, related_name="certificat"
    )
    numero = models.CharField(max_length=50, unique=True)
    code_verification = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date_delivrance = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_delivrance"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
