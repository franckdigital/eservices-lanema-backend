from django.db import models

from dmct_clients.models import ClientDMCT


class InstrumentMesure(models.Model):
    STATUT_CHOICES = [
        ("EN_SERVICE", "En service"),
        ("IMMOBILISE", "Immobilisé"),
    ]

    reference = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=255)
    type_instrument = models.CharField(max_length=255, blank=True)
    client = models.ForeignKey(
        ClientDMCT, on_delete=models.SET_NULL, null=True, blank=True, related_name="instruments"
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_SERVICE")

    class Meta:
        ordering = ["designation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.reference


class CertificatDMCT(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    instrument = models.ForeignKey(InstrumentMesure, on_delete=models.CASCADE, related_name="certificats")
    date_emission = models.DateField(auto_now_add=True)
    date_expiration = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
