from rest_framework import serializers

from .models import FactureDAE


class FactureDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = FactureDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "client", "client_nom",
            "montant_ht", "montant_ttc", "statut", "date_emission", "date_paiement",
        ]
        read_only_fields = ["id", "date_emission"]
