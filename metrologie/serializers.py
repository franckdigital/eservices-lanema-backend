from rest_framework import serializers

from .models import Equipement, Etalonnage, MaintenancePreventive, PanneEquipement


class EquipementSerializer(serializers.ModelSerializer):
    laboratoire_nom = serializers.CharField(source="laboratoire.nom", read_only=True, default=None)

    class Meta:
        model = Equipement
        fields = [
            "id",
            "code",
            "designation",
            "type",
            "marque",
            "modele",
            "date_dernier_etalonnage",
            "date_prochain_etalonnage",
            "localisation",
            "laboratoire",
            "laboratoire_nom",
            "responsable",
            "statut",
        ]


class EtalonnageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etalonnage
        fields = [
            "id",
            "equipement",
            "date_etalonnage",
            "date_prochain",
            "prestataire",
            "resultat",
        ]


class PanneEquipementSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = PanneEquipement
        fields = ["id", "equipement", "equipement_code", "date_panne", "date_reparation", "cout", "description"]
        read_only_fields = ["id", "date_panne"]


class MaintenancePreventiveSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = MaintenancePreventive
        fields = [
            "id", "equipement", "equipement_code", "date_prevue", "date_realisee",
            "statut", "reussie", "observations",
        ]
        read_only_fields = ["id"]
