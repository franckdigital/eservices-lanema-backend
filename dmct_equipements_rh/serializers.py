from rest_framework import serializers

from .models import (
    CertificationAgentDMCT,
    EquipementReference,
    EtalonnageReference,
    FormationDMCT,
    MaintenancePreventiveReference,
    PanneEquipementReference,
)


class EquipementReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipementReference
        fields = [
            "id", "code", "designation", "est_etalon", "statut",
            "date_dernier_etalonnage", "date_prochain_etalonnage",
        ]
        read_only_fields = ["id"]


class PanneEquipementReferenceSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = PanneEquipementReference
        fields = ["id", "equipement", "equipement_code", "date_panne", "date_reparation", "description"]
        read_only_fields = ["id", "date_panne"]


class MaintenancePreventiveReferenceSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = MaintenancePreventiveReference
        fields = ["id", "equipement", "equipement_code", "date_prevue", "date_realisee", "statut"]
        read_only_fields = ["id"]


class EtalonnageReferenceSerializer(serializers.ModelSerializer):
    equipement_code = serializers.CharField(source="equipement.code", read_only=True)

    class Meta:
        model = EtalonnageReference
        fields = ["id", "equipement", "equipement_code", "date_etalonnage", "date_prochain", "resultat"]
        read_only_fields = ["id"]


class CertificationAgentDMCTSerializer(serializers.ModelSerializer):
    agent_nom = serializers.CharField(source="agent.username", read_only=True)
    valide = serializers.BooleanField(read_only=True)

    class Meta:
        model = CertificationAgentDMCT
        fields = ["id", "agent", "agent_nom", "competence", "date_obtention", "date_expiration", "valide"]
        read_only_fields = ["id"]


class FormationDMCTSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormationDMCT
        fields = ["id", "titre", "date_formation", "nombre_participants", "duree_heures"]
        read_only_fields = ["id"]
