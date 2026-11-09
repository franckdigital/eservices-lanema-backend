from rest_framework import serializers

from .models import CreneauDisponibilite, DemandeDevis, EchantillonPrevu, SousTraitantPartenaire


class EchantillonPrevuSerializer(serializers.ModelSerializer):
    class Meta:
        model = EchantillonPrevu
        fields = ["id", "nom", "quantite"]
        read_only_fields = ["id"]


class CreneauDisponibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreneauDisponibilite
        fields = ["id", "date_debut", "date_fin", "delai_jours_ouvres", "label", "actif", "created_at"]
        read_only_fields = ["id", "created_at"]


class SousTraitantPartenaireSerializer(serializers.ModelSerializer):
    type_sous_traitant_display = serializers.CharField(source="get_type_sous_traitant_display", read_only=True)

    class Meta:
        model = SousTraitantPartenaire
        fields = [
            "id", "nom", "specialite", "contact", "type_sous_traitant",
            "type_sous_traitant_display", "actif", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DemandeDevisSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    client_code = serializers.CharField(source="client.client_profile.code_client", read_only=True, default=None)
    echantillons_prevus = EchantillonPrevuSerializer(many=True, read_only=True)
    sous_traitants_choisis_detail = SousTraitantPartenaireSerializer(source="sous_traitants_choisis", many=True, read_only=True)

    class Meta:
        model = DemandeDevis
        fields = [
            "id",
            "numero",
            "client",
            "client_email",
            "client_code",
            "type_analyse",
            "categorie",
            "objet",
            "description",
            "statut",
            "delai_realisation_jours",
            "accord_sous_traitance",
            "sous_traitants_choisis",
            "sous_traitants_choisis_detail",
            "sous_traitants_souhaits_libres",
            "echantillons_prevus",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "statut",
            "numero",
            "client",
            "client_email",
            "client_code",
        ]
