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
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)
    non_conformite_reference = serializers.CharField(source="non_conformite.reference", read_only=True, default=None)

    class Meta:
        model = ActionQualite
        fields = [
            "id", "non_conformite", "non_conformite_reference", "type", "description", "responsable",
            "responsable_nom", "statut", "date_planification", "date_cloture",
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

    def validate(self, attrs):
        # Les KPI "délai moyen de traitement" et "taux de satisfaction client"
        # dépendent de ces deux champs : les rendre obligatoires dès que le
        # statut passe à TRAITEE évite des réclamations "traitées" sans date
        # ni note, qui fausseraient ces indicateurs silencieusement.
        statut = attrs.get("statut", getattr(self.instance, "statut", None))
        if statut == "TRAITEE":
            date_traitement = attrs.get("date_traitement", getattr(self.instance, "date_traitement", None))
            note_satisfaction = attrs.get("note_satisfaction", getattr(self.instance, "note_satisfaction", None))
            if not date_traitement:
                raise serializers.ValidationError({"date_traitement": "Requis lorsque le statut est « Traitée »."})
            if not note_satisfaction:
                raise serializers.ValidationError({"note_satisfaction": "Requise lorsque le statut est « Traitée »."})
        return attrs


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
