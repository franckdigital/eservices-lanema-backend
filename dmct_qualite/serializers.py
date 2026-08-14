from rest_framework import serializers

from .models import ActionCorrectiveDMCT, AuditDMCT, NonConformiteDMCT


class NonConformiteDMCTSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)
    prestation_reference = serializers.CharField(source="prestation.reference", read_only=True, default=None)

    class Meta:
        model = NonConformiteDMCT
        fields = [
            "id", "reference", "prestation", "prestation_reference", "gravite", "description",
            "responsable", "responsable_nom", "statut", "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class ActionCorrectiveDMCTSerializer(serializers.ModelSerializer):
    non_conformite_reference = serializers.CharField(source="non_conformite.reference", read_only=True)
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = ActionCorrectiveDMCT
        fields = [
            "id", "non_conformite", "non_conformite_reference", "description", "responsable",
            "responsable_nom", "statut", "date_prevue", "date_realisation",
        ]
        read_only_fields = ["id"]


class AuditDMCTSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditDMCT
        fields = ["id", "reference", "type_audit", "date_audit", "resultat"]
        read_only_fields = ["id"]
