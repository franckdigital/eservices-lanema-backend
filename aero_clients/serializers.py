from rest_framework import serializers

from .models import Aeronef, ClientAeronautique, ReclamationClientDAE


class ClientAeronautiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAeronautique
        fields = ["id", "nom", "contact", "actif", "created_at"]
        read_only_fields = ["id", "created_at"]


class AeronefSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True, default=None)

    class Meta:
        model = Aeronef
        fields = ["id", "immatriculation", "type_aeronef", "client", "client_nom", "statut"]
        read_only_fields = ["id"]


class ReclamationClientDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)

    class Meta:
        model = ReclamationClientDAE
        fields = [
            "id", "client", "client_nom", "description", "date_reception",
            "date_traitement", "statut", "note_satisfaction",
        ]
        read_only_fields = ["id", "date_reception"]
