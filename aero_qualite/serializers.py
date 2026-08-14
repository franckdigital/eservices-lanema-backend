from rest_framework import serializers

from .models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE


class NonConformiteDAESerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = NonConformiteDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "gravite", "description",
            "responsable", "responsable_nom", "statut", "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class ActionCorrectiveDAESerializer(serializers.ModelSerializer):
    non_conformite_reference = serializers.CharField(source="non_conformite.reference", read_only=True)
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = ActionCorrectiveDAE
        fields = [
            "id", "non_conformite", "non_conformite_reference", "description", "responsable",
            "responsable_nom", "statut", "date_prevue", "date_realisation",
        ]
        read_only_fields = ["id"]


class AuditQualiteDAESerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditQualiteDAE
        fields = ["id", "reference", "type_audit", "date_audit", "resultat"]
        read_only_fields = ["id"]
