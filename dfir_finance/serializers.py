from rest_framework import serializers

from .models import FactureDFIR


class FactureDFIRSerializer(serializers.ModelSerializer):
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True)
    session_titre = serializers.CharField(source="session.formation.titre", read_only=True, default=None)

    class Meta:
        model = FactureDFIR
        fields = [
            "id", "reference", "type_prestation", "session", "session_titre", "mission", "projet_recherche",
            "entreprise", "entreprise_nom", "montant_ht", "montant_ttc", "statut", "date_emission", "date_paiement",
        ]
        read_only_fields = ["id", "date_emission"]
