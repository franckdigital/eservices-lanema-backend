from rest_framework import serializers

from .models import HistoriqueActionDAE, PieceJointeDAE


class HistoriqueActionDAESerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.SerializerMethodField()

    class Meta:
        model = HistoriqueActionDAE
        fields = ["id", "action", "ancienne_valeur", "nouvelle_valeur", "date", "utilisateur_nom"]

    def get_utilisateur_nom(self, obj):
        if not obj.utilisateur:
            return None
        return obj.utilisateur.get_full_name() or obj.utilisateur.username


class PieceJointeDAESerializer(serializers.ModelSerializer):
    uploaded_by_nom = serializers.SerializerMethodField()

    class Meta:
        model = PieceJointeDAE
        fields = ["id", "nom", "fichier", "uploaded_by_nom", "uploaded_at"]
        read_only_fields = ["id", "nom", "uploaded_by_nom", "uploaded_at"]

    def get_uploaded_by_nom(self, obj):
        if not obj.uploaded_by:
            return None
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
