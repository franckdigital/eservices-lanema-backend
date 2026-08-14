from rest_framework import serializers

from .models import CertificatDMCT, InstrumentMesure


class InstrumentMesureSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True, default=None)

    class Meta:
        model = InstrumentMesure
        fields = ["id", "reference", "designation", "type_instrument", "client", "client_nom", "statut"]
        read_only_fields = ["id"]


class CertificatDMCTSerializer(serializers.ModelSerializer):
    instrument_reference = serializers.CharField(source="instrument.reference", read_only=True)

    class Meta:
        model = CertificatDMCT
        fields = ["id", "numero", "instrument", "instrument_reference", "date_emission", "date_expiration"]
        read_only_fields = ["id", "date_emission"]
