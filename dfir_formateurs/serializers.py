from rest_framework import serializers

from .models import FormateurDFIR


class FormateurDFIRSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = FormateurDFIR
        fields = ["id", "user", "user_nom", "specialite", "date_qualification", "disponible"]
        read_only_fields = ["id"]
