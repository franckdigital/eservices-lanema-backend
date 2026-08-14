from rest_framework import serializers

from .models import ContreVisiteDMCT, InspectionDMCT


class InspectionDMCTSerializer(serializers.ModelSerializer):
    etablissement_nom = serializers.CharField(source="etablissement.nom", read_only=True, default=None)

    class Meta:
        model = InspectionDMCT
        fields = [
            "id", "reference", "etablissement", "etablissement_nom", "categorie", "type_controle",
            "date_inspection", "date_cloture", "conforme", "sanction_emise", "observations",
        ]
        read_only_fields = ["id", "date_inspection"]


class ContreVisiteDMCTSerializer(serializers.ModelSerializer):
    inspection_reference = serializers.CharField(source="inspection.reference", read_only=True)

    class Meta:
        model = ContreVisiteDMCT
        fields = ["id", "inspection", "inspection_reference", "date_contre_visite", "resultat"]
        read_only_fields = ["id"]
