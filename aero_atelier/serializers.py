from rest_framework import serializers

from .models import (
    CertificationTechnicien,
    EquipementAtelier,
    EtalonnageAtelier,
    MaintenancePreventiveAtelier,
    PanneEquipementAtelier,
)


class EquipementAtelierSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipementAtelier
        fields = ["id", "code", "designation", "statut"]
        read_only_fields = ["id"]


class PanneEquipementAtelierSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = PanneEquipementAtelier
        fields = ["id", "equipement", "equipement_code", "date_panne", "date_reparation", "description"]
        read_only_fields = ["id", "date_panne"]


class MaintenancePreventiveAtelierSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = MaintenancePreventiveAtelier
        fields = ["id", "equipement", "equipement_code", "date_prevue", "date_realisee", "statut"]
        read_only_fields = ["id"]


class EtalonnageAtelierSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = EtalonnageAtelier
        fields = ["id", "equipement", "equipement_code", "date_etalonnage", "date_prochain", "resultat"]
        read_only_fields = ["id"]


class CertificationTechnicienSerializer(serializers.ModelSerializer):
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True)
    valide = serializers.BooleanField(read_only=True)

    class Meta:
        model = CertificationTechnicien
        fields = ["id", "technicien", "technicien_nom", "competence", "date_obtention", "date_expiration", "valide"]
        read_only_fields = ["id"]
