from rest_framework import serializers

from .models import Aeronef, ClientAeronautique, DemandeDAE, ReclamationClientDAE, SatisfactionDAE


class ClientAeronautiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAeronautique
        fields = [
            "id", "code", "nom", "type_client", "adresse", "telephone", "email",
            "numero_identification", "contact", "actif", "created_at",
        ]
        read_only_fields = ["id", "code", "created_at"]


class AeronefSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True, default=None)

    class Meta:
        model = Aeronef
        fields = [
            "id", "immatriculation", "type_aeronef", "constructeur", "modele", "numero_serie",
            "proprietaire", "annee_fabrication", "nombre_heures_vol", "nombre_cycles",
            "client", "client_nom", "statut",
        ]
        read_only_fields = ["id"]


class ReclamationClientDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)
    type_reclamation_label = serializers.CharField(source="get_type_reclamation_display", read_only=True)

    class Meta:
        model = ReclamationClientDAE
        fields = [
            "id", "reference", "client", "client_nom", "ordre_travail", "ordre_travail_reference",
            "type_reclamation", "type_reclamation_label", "description", "analyse", "responsable",
            "responsable_nom", "reponse", "date_reception", "date_reponse", "date_traitement",
            "statut", "note_satisfaction",
        ]
        # "reference" est auto-generee. "statut" doit passer par l'action
        # changer_statut (verrou : affectation avant traitement, reponse
        # avant cloture) — cf. cahier des charges DAE section 22.
        read_only_fields = ["id", "reference", "date_reception", "statut"]


class SatisfactionDAESerializer(serializers.ModelSerializer):
    """Vue staff (liste/gestion) de la fiche de satisfaction."""

    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True)
    client_nom = serializers.CharField(source="ordre_travail.aeronef.client.nom", read_only=True, default=None)
    note_moyenne = serializers.FloatField(read_only=True)

    class Meta:
        model = SatisfactionDAE
        fields = [
            "id", "ordre_travail", "ordre_travail_reference", "client_nom", "token",
            "note_qualite", "note_delai", "note_accueil", "note_communication", "note_prestation_technique",
            "note_moyenne", "commentaire", "date_envoi", "date_evaluation",
        ]
        read_only_fields = ["id", "token", "date_envoi", "date_evaluation"]


class SatisfactionDAEPublicSerializer(serializers.ModelSerializer):
    """Vue publique (lien sans compte) : contexte minimal pour le formulaire."""

    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True)
    aeronef_immatriculation = serializers.CharField(source="ordre_travail.aeronef.immatriculation", read_only=True, default=None)
    client_nom = serializers.CharField(source="ordre_travail.aeronef.client.nom", read_only=True, default=None)
    deja_evalue = serializers.SerializerMethodField()

    def get_deja_evalue(self, obj):
        return obj.date_evaluation is not None

    class Meta:
        model = SatisfactionDAE
        fields = ["ordre_travail_reference", "aeronef_immatriculation", "client_nom", "deja_evalue"]


class DemandeDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    aeronef_immatriculation = serializers.CharField(source="aeronef.immatriculation", read_only=True, default=None)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = DemandeDAE
        fields = [
            "id", "reference", "client", "client_nom", "aeronef", "aeronef_immatriculation",
            "type_intervention", "description", "urgence", "statut",
            "date_reception", "date_traitement", "ordre_travail", "ordre_travail_reference", "cree_par",
        ]
        read_only_fields = ["id", "reference", "date_reception", "date_traitement", "ordre_travail", "cree_par"]
