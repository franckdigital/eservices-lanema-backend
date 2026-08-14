from rest_framework import serializers

from .models import Rapport, RapportEssai


class RapportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rapport
        fields = [
            "id",
            "type_rapport",
            "titre",
            "parametres",
            "cree_par",
            "date_creation",
        ]
        read_only_fields = ["id", "date_creation", "cree_par"]


class RapportEssaiSerializer(serializers.ModelSerializer):
    essai_numero = serializers.CharField(source="essai.numero", read_only=True)
    valide_par_nom = serializers.CharField(source="valide_par.username", read_only=True, default=None)

    class Meta:
        model = RapportEssai
        fields = [
            "id", "essai", "essai_numero", "statut", "date_creation", "date_soumission",
            "date_validation", "valide_par", "valide_par_nom", "signe_electroniquement",
            "date_signature", "delai_reglementaire_jours",
        ]
        read_only_fields = ["id", "date_creation"]
