from rest_framework import serializers

from .models import ClientDMCT, ReclamationClientDMCT


class ClientDMCTSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDMCT
        fields = ["id", "nom", "secteur_activite", "contact", "actif", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReclamationClientDMCTSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)

    class Meta:
        model = ReclamationClientDMCT
        fields = [
            "id", "client", "client_nom", "description", "date_reception",
            "date_traitement", "statut", "note_satisfaction",
        ]
        read_only_fields = ["id", "date_reception"]
