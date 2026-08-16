from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Deux modeles transverses a toute la DAE (traçabilite + pieces jointes),
# rattaches par GenericForeignKey plutot que dupliques par app — reutilisables
# sur OrdreTravail, DemandeDAE, NonConformiteDAE, ActionCorrectiveDAE,
# FactureDAE, etc. sans creer un modele Historique/PieceJointe par app.
# Cet agregateur reste par ailleurs sans modele metier propre (KPI uniquement,
# cf. commentaire precedent conserve ci-dessous par les autres fichiers de
# cette app).


class HistoriqueActionDAE(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    action = models.CharField(max_length=255)
    ancienne_valeur = models.CharField(max_length=255, blank=True)
    nouvelle_valeur = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.action} - {self.date}"


class PieceJointeDAE(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    fichier = models.FileField(upload_to="dae/pieces_jointes/%Y/%m/")
    nom = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def save(self, *args, **kwargs):
        if not self.nom and self.fichier:
            self.nom = self.fichier.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.nom
