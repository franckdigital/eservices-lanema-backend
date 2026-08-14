from rest_framework import serializers

from .models import ObjectifStrategique


class ObjectifStrategiqueSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True, default=None)
    service_nom = serializers.CharField(source="service.nom", read_only=True, default=None)
    taux_realisation = serializers.FloatField(read_only=True)

    class Meta:
        model = ObjectifStrategique
        fields = [
            "id", "type", "nom", "direction", "direction_nom", "service", "service_nom",
            "cible", "valeur_actuelle", "periode", "statut", "taux_realisation",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
