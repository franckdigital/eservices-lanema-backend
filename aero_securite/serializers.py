from rest_framework import serializers

from .models import ControleReglementaire, EcartReglementaire, FormationSecurite, IncidentTechnique, RapportSecurite


class IncidentTechniqueSerializer(serializers.ModelSerializer):
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = IncidentTechnique
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "gravite",
            "description", "date_incident", "est_accident",
        ]
        read_only_fields = ["id", "date_incident"]


class EcartReglementaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcartReglementaire
        fields = ["id", "reference", "description", "date_constat", "resolu"]
        read_only_fields = ["id", "date_constat"]


class RapportSecuriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RapportSecurite
        fields = ["id", "reference", "date_creation", "description"]
        read_only_fields = ["id", "date_creation"]


class ControleReglementaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControleReglementaire
        fields = ["id", "reference", "organisme", "date_controle", "resultat"]
        read_only_fields = ["id"]


class FormationSecuriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormationSecurite
        fields = ["id", "titre", "date_formation", "nombre_participants", "duree_heures"]
        read_only_fields = ["id"]
