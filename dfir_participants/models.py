from django.conf import settings
from django.db import models


class EntrepriseDFIR(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    secteur_activite = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self) -> str:  # pragma: no cover
        return self.nom


class ParticipantDFIR(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True)
    entreprise = models.ForeignKey(
        EntrepriseDFIR, on_delete=models.SET_NULL, null=True, blank=True, related_name="participants"
    )
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Compte "mon espace e-learning" : cree a l'inscription du participant (email +
    # mot de passe), independant des comptes e-diligence/labo. Nullable car des
    # ParticipantDFIR peuvent deja exister (saisis par le staff) avant que la
    # personne ne cree elle-meme son compte avec la meme adresse email.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="participant_dfir_profile",
    )

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.prenom} {self.nom}".strip()
