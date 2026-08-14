from rest_framework import serializers

from .models import PieceComptable


class PieceComptableSerializer(serializers.ModelSerializer):
    valide_par_nom = serializers.CharField(source="valide_par.username", read_only=True, default=None)

    class Meta:
        model = PieceComptable
        fields = [
            "id", "numero", "type_piece", "source_reference", "montant", "date_piece",
            "fichier", "statut", "valide_par", "valide_par_nom", "date_validation",
        ]
        read_only_fields = ["id", "date_piece", "valide_par", "date_validation"]
