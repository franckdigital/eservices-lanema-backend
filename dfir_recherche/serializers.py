from rest_framework import serializers

from .models import (
    CollaborationRecherche,
    ProjetRecherche,
    PublicationScientifique,
    RapportRecherche,
    RecommandationRecherche,
)


class ProjetRechercheSerializer(serializers.ModelSerializer):
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True, default=None)

    class Meta:
        model = ProjetRecherche
        fields = [
            "id", "reference", "titre", "type_projet", "entreprise", "entreprise_nom",
            "date_debut", "date_fin_prevue", "date_fin_reelle", "statut",
        ]
        read_only_fields = ["id", "date_debut"]


class PublicationScientifiqueSerializer(serializers.ModelSerializer):
    projet_reference = serializers.CharField(source="projet.reference", read_only=True, default=None)

    class Meta:
        model = PublicationScientifique
        fields = ["id", "projet", "projet_reference", "titre", "date_publication"]
        read_only_fields = ["id"]


class RapportRechercheSerializer(serializers.ModelSerializer):
    projet_reference = serializers.CharField(source="projet.reference", read_only=True)

    class Meta:
        model = RapportRecherche
        fields = ["id", "projet", "projet_reference", "titre", "date_creation", "valide", "date_validation"]
        read_only_fields = ["id", "date_creation"]


class RecommandationRechercheSerializer(serializers.ModelSerializer):
    rapport_titre = serializers.CharField(source="rapport.titre", read_only=True)

    class Meta:
        model = RecommandationRecherche
        fields = ["id", "rapport", "rapport_titre", "description", "appliquee"]
        read_only_fields = ["id"]


class CollaborationRechercheSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborationRecherche
        fields = ["id", "nom_partenaire", "type_partenaire", "date_debut"]
        read_only_fields = ["id"]
