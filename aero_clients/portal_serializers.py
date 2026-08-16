"""Serializers du portail client DAE — cf. cahier des charges section 3.7 :
vues volontairement allegees par rapport aux serializers staff (pas de
donnees internes : couts, pieces, technicien assigne...)."""
from rest_framework import serializers

from aero_finance.models import FactureDAE
from aero_maintenance.models import OrdreTravail

from .models import Aeronef, ClientAeronautique, DemandeDAE, ReclamationClientDAE


class ClientPortalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAeronautique
        fields = [
            "id", "code", "nom", "type_client", "adresse", "telephone", "email",
            "numero_identification", "contact",
        ]
        read_only_fields = ["id", "code", "nom"]


class ClientPortalRegisterSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=255)
    type_client = serializers.ChoiceField(choices=ClientAeronautique.TYPE_CHOICES, default="AUTRE")
    adresse = serializers.CharField(max_length=255, required=False, allow_blank=True)
    telephone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    numero_identification = serializers.CharField(max_length=100, required=False, allow_blank=True)
    contact = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)


class ClientPortalAeronefSerializer(serializers.ModelSerializer):
    """Le client peut declarer ses propres aeronefs (identification uniquement)
    — heures de vol/cycles/statut restent pilotes par la DAE au fil des
    interventions, pas saisis par le client."""

    class Meta:
        model = Aeronef
        fields = [
            "id", "immatriculation", "type_aeronef", "constructeur", "modele", "numero_serie",
            "annee_fabrication", "nombre_heures_vol", "nombre_cycles", "statut",
        ]
        read_only_fields = ["id", "nombre_heures_vol", "nombre_cycles", "statut"]


class ClientPortalDemandeSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = DemandeDAE
        fields = [
            "id", "reference", "aeronef", "aeronef_immatriculation", "type_intervention", "description",
            "urgence", "statut", "date_reception", "date_traitement", "ordre_travail", "ordre_travail_reference",
        ]
        read_only_fields = ["id", "reference", "statut", "date_reception", "date_traitement", "ordre_travail"]


class ClientPortalOrdreTravailSerializer(serializers.ModelSerializer):
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True)
    statut_label = serializers.CharField(source="get_statut_display", read_only=True)
    numero_certificat = serializers.SerializerMethodField()

    def get_numero_certificat(self, obj):
        return getattr(getattr(obj, "certificat", None), "numero", None)

    class Meta:
        model = OrdreTravail
        fields = [
            "id", "reference", "aeronef", "aeronef_immatriculation", "type_intervention",
            "date_demande", "date_debut", "date_fin_prevue", "date_fin", "statut", "statut_label",
            "numero_certificat",
        ]
        read_only_fields = fields


class ClientPortalFactureSerializer(serializers.ModelSerializer):
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = FactureDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "montant_ht", "montant_ttc",
            "statut", "date_emission", "date_paiement",
        ]
        read_only_fields = fields


class ClientPortalReclamationSerializer(serializers.ModelSerializer):
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)
    type_reclamation_label = serializers.CharField(source="get_type_reclamation_display", read_only=True)

    class Meta:
        model = ReclamationClientDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "type_reclamation",
            "type_reclamation_label", "description", "reponse", "date_reception", "date_reponse",
            "statut", "note_satisfaction",
        ]
        read_only_fields = [
            "id", "reference", "reponse", "date_reception", "date_reponse", "statut",
        ]
