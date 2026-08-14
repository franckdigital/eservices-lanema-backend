from rest_framework import serializers

from .models import BatterieAeronef, InspectionRoue, OrdreTravail, RoueAeronef


class OrdreTravailSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True)
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True, default=None)

    class Meta:
        model = OrdreTravail
        fields = [
            "id", "reference", "aeronef", "aeronef_immatriculation", "type_intervention",
            "technicien", "technicien_nom", "date_demande", "date_prise_charge", "date_debut",
            "date_fin_prevue", "date_fin", "statut", "piece_utilisee",
        ]
        read_only_fields = ["id", "date_demande"]


class RoueAeronefSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)

    class Meta:
        model = RoueAeronef
        fields = ["id", "numero_serie", "aeronef", "aeronef_immatriculation", "statut", "nombre_cycles"]
        read_only_fields = ["id"]


class InspectionRoueSerializer(serializers.ModelSerializer):
    roue_numero_serie = serializers.CharField(source="roue.numero_serie", read_only=True)

    class Meta:
        model = InspectionRoue
        fields = [
            "id", "roue", "roue_numero_serie", "ordre_travail", "date_inspection",
            "conforme", "type_inspection",
        ]
        read_only_fields = ["id", "date_inspection"]


class BatterieAeronefSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)

    class Meta:
        model = BatterieAeronef
        fields = [
            "id", "numero_serie", "aeronef", "aeronef_immatriculation", "statut",
            "date_mise_en_service", "date_derniere_maintenance",
        ]
        read_only_fields = ["id"]
