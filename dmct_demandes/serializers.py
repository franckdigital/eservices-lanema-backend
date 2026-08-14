from rest_framework import serializers

from .models import DemandeDMCT


class DemandeDMCTSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)

    class Meta:
        model = DemandeDMCT
        fields = [
            "id", "reference", "type_demande", "client", "client_nom", "date_demande",
            "date_enregistrement", "date_prise_charge", "date_limite_prise_charge", "statut",
        ]
        read_only_fields = ["id", "date_demande"]
