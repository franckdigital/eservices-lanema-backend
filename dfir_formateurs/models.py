from django.conf import settings
from django.db import models


class FormateurDFIR(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="formateur_dfir")
    specialite = models.CharField(max_length=255, blank=True)
    date_qualification = models.DateField()
    disponible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date_qualification"]

    def __str__(self) -> str:  # pragma: no cover
        return str(self.user)
