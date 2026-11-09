from rest_framework import serializers

from .models import DemandeDevis, EchantillonPrevu


class EchantillonPrevuSerializer(serializers.ModelSerializer):
    class Meta:
        model = EchantillonPrevu
        fields = ["id", "nom", "quantite"]
        read_only_fields = ["id"]


class DemandeDevisSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    client_code = serializers.CharField(source="client.client_profile.code_client", read_only=True, default=None)
    echantillons_prevus = EchantillonPrevuSerializer(many=True, read_only=True)

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
