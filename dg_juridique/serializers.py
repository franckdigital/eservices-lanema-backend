from rest_framework import serializers

from .models import (
    AvisJuridique,
    Contentieux,
    Contrat,
    DossierJuridique,
    ProcedureDisciplinaire,
    TexteReglementaire,
)


class DossierJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierJuridique
        fields = [
            "id", "reference", "type_dossier", "titre", "description", "statut",
            "date_ouverture", "date_cloture", "responsable",
        ]
        read_only_fields = ["id", "reference", "date_ouverture"]


class ContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrat
        fields = [
            "id", "dossier", "reference", "intitule", "partie_prenante", "statut",
            "date_redaction", "date_validation", "date_signature", "date_expiration",
        ]
        read_only_fields = ["id", "reference", "date_redaction"]


class ContentieuxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contentieux
        fields = [
            "id", "dossier", "reference", "partie_adverse", "objet", "statut", "issue",
            "date_ouverture", "date_cloture",
        ]
        read_only_fields = ["id", "reference", "date_ouverture"]


class AvisJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvisJuridique
        fields = ["id", "dossier", "demandeur", "sujet", "date_demande", "date_reponse", "reponse"]
        read_only_fields = ["id", "date_demande"]


class ProcedureDisciplinaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureDisciplinaire
        fields = ["id", "reference", "agent_concerne", "motif", "statut", "date_ouverture", "date_cloture"]
        read_only_fields = ["id", "reference", "date_ouverture"]


class TexteReglementaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = TexteReglementaire
        fields = [
            "id", "reference", "intitule", "dossier", "statut", "date_analyse",
            "synthese", "analyse_par",
        ]
        read_only_fields = ["id", "date_analyse"]
