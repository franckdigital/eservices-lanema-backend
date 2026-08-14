from rest_framework import serializers

from .models import DemandeDevis


class DemandeDevisSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)

    class Meta:
        model = DemandeDevis
        fields = [
            "id",
            "numero",
            "client",
            "client_email",
            "type_analyse",
            "categorie",
            "objet",
            "description",
            "statut",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "statut",
            "numero",
            "client",
            "client_email",
        ]
