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
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = DossierJuridique
        fields = [
            "id", "reference", "type_dossier", "titre", "description", "statut",
            "date_ouverture", "date_cloture", "responsable", "responsable_nom",
        ]
        read_only_fields = ["id", "reference", "date_ouverture"]


class ContratSerializer(serializers.ModelSerializer):
    dossier_reference = serializers.CharField(source="dossier.reference", read_only=True, default=None)

    class Meta:
        model = Contrat
        fields = [
            "id", "dossier", "dossier_reference", "reference", "intitule", "partie_prenante", "statut",
            "date_redaction", "date_validation", "date_signature", "date_expiration",
        ]
        read_only_fields = ["id", "reference", "date_redaction"]


class ContentieuxSerializer(serializers.ModelSerializer):
    dossier_reference = serializers.CharField(source="dossier.reference", read_only=True, default=None)

    class Meta:
        model = Contentieux
        fields = [
            "id", "dossier", "dossier_reference", "reference", "partie_adverse", "objet", "statut", "issue",
            "date_ouverture", "date_cloture",
        ]
        read_only_fields = ["id", "reference", "date_ouverture"]


class AvisJuridiqueSerializer(serializers.ModelSerializer):
    dossier_reference = serializers.CharField(source="dossier.reference", read_only=True, default=None)
    demandeur_nom = serializers.CharField(source="demandeur.username", read_only=True, default=None)

    class Meta:
        model = AvisJuridique
        fields = ["id", "dossier", "dossier_reference", "demandeur", "demandeur_nom", "sujet", "date_demande", "date_reponse", "reponse"]
        read_only_fields = ["id", "date_demande"]


class ProcedureDisciplinaireSerializer(serializers.ModelSerializer):
    agent_concerne_nom = serializers.CharField(source="agent_concerne.username", read_only=True, default=None)

    class Meta:
        model = ProcedureDisciplinaire
        fields = ["id", "reference", "agent_concerne", "agent_concerne_nom", "motif", "statut", "date_ouverture", "date_cloture"]
        read_only_fields = ["id", "reference", "date_ouverture"]


class TexteReglementaireSerializer(serializers.ModelSerializer):
    dossier_reference = serializers.CharField(source="dossier.reference", read_only=True, default=None)
    analyse_par_nom = serializers.CharField(source="analyse_par.username", read_only=True, default=None)

    class Meta:
        model = TexteReglementaire
        fields = [
            "id", "reference", "intitule", "dossier", "dossier_reference", "statut", "date_analyse",
            "synthese", "analyse_par", "analyse_par_nom",
        ]
        read_only_fields = ["id", "date_analyse"]
