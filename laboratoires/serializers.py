from rest_framework import serializers

from .models import Laboratoire


class LaboratoireSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = Laboratoire
        fields = ["id", "nom", "code", "responsable", "responsable_nom", "capacite_journaliere", "created_at"]
        read_only_fields = ["id", "created_at"]
