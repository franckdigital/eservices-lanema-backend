from rest_framework import serializers

from .models import MissionAssistance


class MissionAssistanceSerializer(serializers.ModelSerializer):
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True)

    class Meta:
        model = MissionAssistance
        fields = [
            "id", "reference", "entreprise", "entreprise_nom", "date_demande", "date_debut", "date_fin",
            "statut", "diagnostic_realise", "plan_amelioration_elabore", "satisfaction",
        ]
        read_only_fields = ["id", "date_demande"]
