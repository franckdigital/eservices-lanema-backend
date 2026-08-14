from rest_framework import serializers

from .models import FactureDMCT


class FactureDMCTSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    prestation_reference = serializers.CharField(source="prestation.reference", read_only=True, default=None)

    class Meta:
        model = FactureDMCT
        fields = [
            "id", "reference", "prestation", "prestation_reference", "client", "client_nom",
            "montant_ht", "montant_ttc", "statut", "date_emission", "date_paiement",
        ]
        read_only_fields = ["id", "date_emission"]
