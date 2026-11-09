from rest_framework import serializers

from .models import (
    CreneauDisponibilite,
    DemandeDevis,
    EchantillonPrevu,
    InterventionPrelevement,
    SousTraitantPartenaire,
)


class EchantillonPrevuSerializer(serializers.ModelSerializer):
    class Meta:
        model = EchantillonPrevu
        fields = ["id", "nom", "quantite", "methode_utilisee", "prix_unitaire", "sous_traite"]
        read_only_fields = ["id"]


class InterventionPrelevementSerializer(serializers.ModelSerializer):
    designation_display = serializers.CharField(source="get_designation_display", read_only=True)
    montant = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InterventionPrelevement
        fields = [
            "id", "designation", "designation_display", "duree_heures", "km",
            "nombre", "prix_unitaire", "montant",
        ]
        read_only_fields = ["id", "designation_display", "montant"]


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
    client_adresse = serializers.CharField(source="client.client_profile.adresse", read_only=True, default=None)
    client_domaine_activite = serializers.CharField(source="client.client_profile.domaine_activite", read_only=True, default=None)
    client_situation_geographique = serializers.CharField(source="client.client_profile.situation_geographique", read_only=True, default=None)
    client_contact_nom = serializers.CharField(source="client.client_profile.contact_nom", read_only=True, default=None)
    client_telephone = serializers.CharField(source="client.client_profile.telephone", read_only=True, default=None)
    echantillons_prevus = EchantillonPrevuSerializer(many=True, read_only=True)
    sous_traitants_choisis_detail = SousTraitantPartenaireSerializer(source="sous_traitants_choisis", many=True, read_only=True)
    interventions_prelevement = InterventionPrelevementSerializer(many=True, read_only=True)

    class Meta:
        model = DemandeDevis
        fields = [
            "id",
            "numero",
            "client",
            "client_email",
            "client_code",
            "client_adresse",
            "client_domaine_activite",
            "client_situation_geographique",
            "client_contact_nom",
            "client_telephone",
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
            "retour_materiel_gere_labo",
            "lieu_realisation",
            "observations_particulieres",
            "declaration_conformite_souhaitee",
            "regle_decision",
            "echantillons_prevus",
            "interventions_prelevement",
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
            "client_adresse",
            "client_domaine_activite",
            "client_situation_geographique",
            "client_contact_nom",
            "client_telephone",
        ]
