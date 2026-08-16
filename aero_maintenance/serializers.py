from rest_framework import serializers

from .models import (
    BatterieAeronef,
    CertificatDAE,
    EquipementAeronautique,
    InspectionRoue,
    InterventionTechnique,
    OrdreTravail,
    RoueAeronef,
    TestBatterie,
)


class EquipementAeronautiqueSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)
    type_equipement_label = serializers.CharField(source="get_type_equipement_display", read_only=True)

    class Meta:
        model = EquipementAeronautique
        fields = [
            "id", "reference", "numero_serie", "type_equipement", "type_equipement_label", "fabricant", "modele",
            "proprietaire", "aeronef", "aeronef_immatriculation", "statut", "date_reception",
        ]
        read_only_fields = ["id", "date_reception"]


class OrdreTravailSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True)
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True, default=None)
    non_conformites_ouvertes_count = serializers.SerializerMethodField()
    numero_certificat = serializers.SerializerMethodField()

    def get_non_conformites_ouvertes_count(self, obj):
        return obj.non_conformites.exclude(statut="CLOTUREE").count()

    def get_numero_certificat(self, obj):
        return getattr(getattr(obj, "certificat", None), "numero", None)

    class Meta:
        model = OrdreTravail
        fields = [
            "id", "reference", "aeronef", "aeronef_immatriculation", "type_intervention",
            "technicien", "technicien_nom", "date_demande", "date_prise_charge", "date_debut",
            "date_fin_prevue", "date_fin", "statut", "piece_utilisee", "non_conformites_ouvertes_count",
            "numero_certificat",
        ]
        # "statut" est en lecture seule ici : toute transition doit passer par
        # l'action changer_statut (verrou controle qualite + workflow valide),
        # jamais par un PATCH direct qui contournerait le controle.
        read_only_fields = ["id", "date_demande", "statut"]


class InterventionTechniqueSerializer(serializers.ModelSerializer):
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True, default=None)
    operation_label = serializers.CharField(source="get_operation_display", read_only=True)
    pieces_utilisees_detail = serializers.SerializerMethodField()

    def get_pieces_utilisees_detail(self, obj):
        return [{"id": p.id, "reference": p.reference, "designation": p.designation} for p in obj.pieces_utilisees.all()]

    class Meta:
        model = InterventionTechnique
        fields = [
            "id", "ordre_travail", "technicien", "technicien_nom", "operation", "operation_label",
            "description", "temps_passe_minutes", "mesures", "resultat", "observations",
            "pieces_utilisees", "pieces_utilisees_detail", "date_intervention",
        ]
        read_only_fields = ["id", "technicien", "date_intervention"]


class RoueAeronefSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)

    class Meta:
        model = RoueAeronef
        fields = [
            "id", "reference", "numero_serie", "constructeur", "type_roue", "aeronef", "aeronef_immatriculation",
            "statut", "nombre_cycles", "date_derniere_intervention", "prochaine_inspection",
        ]
        read_only_fields = ["id"]


class InspectionRoueSerializer(serializers.ModelSerializer):
    roue_numero_serie = serializers.CharField(source="roue.numero_serie", read_only=True)
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True, default=None)
    type_inspection_label = serializers.CharField(source="get_type_inspection_display", read_only=True)

    class Meta:
        model = InspectionRoue
        fields = [
            "id", "roue", "roue_numero_serie", "ordre_travail", "technicien", "technicien_nom", "date_inspection",
            "conforme", "type_inspection", "type_inspection_label", "observations",
        ]
        read_only_fields = ["id", "technicien", "date_inspection"]


class BatterieAeronefSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)

    class Meta:
        model = BatterieAeronef
        fields = [
            "id", "reference", "numero_serie", "type_batterie", "capacite_nominale", "tension_nominale",
            "aeronef", "aeronef_immatriculation", "statut", "date_mise_en_service", "date_derniere_maintenance",
            "prochain_controle",
        ]
        read_only_fields = ["id"]


class TestBatterieSerializer(serializers.ModelSerializer):
    batterie_numero_serie = serializers.CharField(source="batterie.numero_serie", read_only=True)
    technicien_nom = serializers.CharField(source="technicien.username", read_only=True, default=None)
    resultat_label = serializers.CharField(source="get_resultat_display", read_only=True)

    class Meta:
        model = TestBatterie
        fields = [
            "id", "batterie", "batterie_numero_serie", "ordre_travail", "technicien", "technicien_nom",
            "date_test", "tension_mesuree", "capacite_mesuree", "etat", "temperature", "charge", "decharge",
            "resultat", "resultat_label", "observations",
        ]
        read_only_fields = ["id", "technicien", "date_test"]
