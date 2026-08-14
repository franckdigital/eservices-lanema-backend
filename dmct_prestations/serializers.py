from rest_framework import serializers

from .models import PrestationDMCT


class PrestationDMCTSerializer(serializers.ModelSerializer):
    instrument_reference = serializers.CharField(source="instrument.reference", read_only=True, default=None)
    demande_reference = serializers.CharField(source="demande.reference", read_only=True, default=None)
    agent_nom = serializers.CharField(source="agent.username", read_only=True, default=None)

    class Meta:
        model = PrestationDMCT
        fields = [
            "id", "reference", "demande", "demande_reference", "instrument", "instrument_reference",
            "type_prestation", "lieu", "agent", "agent_nom", "conforme", "urgent",
            "date_debut", "date_fin", "date_fin_prevue", "date_livraison_certificat",
            "cout_revient", "statut",
        ]
        read_only_fields = ["id"]
