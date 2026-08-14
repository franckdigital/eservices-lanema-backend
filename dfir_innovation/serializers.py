from rest_framework import serializers

from .models import ProjetInnovation


class ProjetInnovationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjetInnovation
        fields = [
            "id", "reference", "titre", "date_lancement", "date_fin_prevue", "date_fin_reelle",
            "statut", "methode_developpee", "prototype_realise", "mis_en_oeuvre", "partenariat",
        ]
        read_only_fields = ["id", "date_lancement"]
