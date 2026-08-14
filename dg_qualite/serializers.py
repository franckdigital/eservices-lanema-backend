from rest_framework import serializers

from .models import (
    ActionQualite,
    AuditQualite,
    IndicateurQualite,
    NonConformiteQualite,
    ReclamationClient,
    RevueDirection,
)


class NonConformiteQualiteSerializer(serializers.ModelSerializer):
    service_nom = serializers.CharField(source="service_concerne.nom", read_only=True, default=None)

    class Meta:
        model = NonConformiteQualite
        fields = [
            "id", "reference", "description", "gravite", "service_concerne", "service_nom",
            "statut", "date_detection", "date_cloture",
        ]
        read_only_fields = ["id", "reference", "date_detection"]


class ActionQualiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionQualite
        fields = [
            "id", "non_conformite", "type", "description", "responsable",
            "statut", "date_planification", "date_cloture",
        ]
        read_only_fields = ["id", "date_planification"]


class AuditQualiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditQualite
        fields = ["id", "reference", "type_audit", "organisme", "date_audit", "resultat", "observations"]
        read_only_fields = ["id"]


class ReclamationClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReclamationClient
        fields = [
            "id", "client_nom", "description", "date_reception", "date_traitement",
            "statut", "note_satisfaction",
        ]
        read_only_fields = ["id", "date_reception"]


class RevueDirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevueDirection
        fields = ["id", "date_revue", "participants", "decisions", "created_at"]
        read_only_fields = ["id", "created_at"]


class IndicateurQualiteSerializer(serializers.ModelSerializer):
    atteint = serializers.BooleanField(read_only=True)

    class Meta:
        model = IndicateurQualite
        fields = ["id", "nom", "cible", "valeur_actuelle", "periode", "atteint"]
        read_only_fields = ["id"]
