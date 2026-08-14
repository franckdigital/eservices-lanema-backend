from rest_framework import serializers

from .models import AmeliorationProgramme, AuditDFIR, ReclamationDFIR


class ReclamationDFIRSerializer(serializers.ModelSerializer):
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True, default=None)
    participant_nom = serializers.CharField(source="participant.__str__", read_only=True, default=None)

    class Meta:
        model = ReclamationDFIR
        fields = [
            "id", "entreprise", "entreprise_nom", "participant", "participant_nom",
            "description", "date_reception", "date_traitement", "statut",
        ]
        read_only_fields = ["id", "date_reception"]


class AmeliorationProgrammeSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="formation.titre", read_only=True, default=None)

    class Meta:
        model = AmeliorationProgramme
        fields = ["id", "formation", "formation_titre", "description", "date_mise_en_oeuvre"]
        read_only_fields = ["id", "date_mise_en_oeuvre"]


class AuditDFIRSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditDFIR
        fields = ["id", "reference", "type_audit", "date_audit", "resultat"]
        read_only_fields = ["id"]
