from rest_framework import serializers

from .models import MouvementPieceRechange, PieceRechange


class PieceRechangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceRechange
        fields = [
            "id", "reference", "designation", "categorie", "quantite_stock",
            "seuil_alerte", "prix_unitaire", "est_critique",
        ]
        read_only_fields = ["id"]


class MouvementPieceRechangeSerializer(serializers.ModelSerializer):
    piece_reference = serializers.CharField(source="piece.reference", read_only=True)

    class Meta:
        model = MouvementPieceRechange
        fields = ["id", "piece", "piece_reference", "type_mouvement", "quantite", "date"]
        read_only_fields = ["id", "date"]
