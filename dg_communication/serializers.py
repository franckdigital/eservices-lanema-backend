from rest_framework import serializers

from .models import ActionCommunication, Partenariat, Prospect, SatisfactionClient


class ActionCommunicationSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = ActionCommunication
        fields = [
            "id", "type", "titre", "description", "date_debut", "date_fin", "statut",
            "budget", "chiffre_affaires_genere", "responsable", "responsable_nom", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProspectSerializer(serializers.ModelSerializer):
    action_origine_titre = serializers.CharField(source="action_origine.titre", read_only=True, default=None)

    class Meta:
        model = Prospect
        fields = [
            "id", "nom", "organisation", "contact_email", "contact_telephone", "source",
            "action_origine", "action_origine_titre", "statut", "montant_devis",
            "date_creation", "date_conversion",
        ]
        read_only_fields = ["id", "date_creation"]


class PartenariatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partenariat
        fields = ["id", "nom_partenaire", "description", "date_signature", "statut", "responsable", "created_at"]
        read_only_fields = ["id", "created_at"]


class SatisfactionClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = SatisfactionClient
        fields = ["id", "client_nom", "note", "fidele", "commentaire", "date_enquete"]
        read_only_fields = ["id", "date_enquete"]
