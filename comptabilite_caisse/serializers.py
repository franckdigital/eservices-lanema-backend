from rest_framework import serializers

from .models import Caisse, MouvementCaisse


class CaisseSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = Caisse
        fields = ["id", "nom", "responsable", "responsable_nom", "solde_initial", "actif"]
        read_only_fields = ["id"]


class MouvementCaisseSerializer(serializers.ModelSerializer):
    caisse_nom = serializers.CharField(source="caisse.nom", read_only=True)

    class Meta:
        model = MouvementCaisse
        fields = [
            "id", "caisse", "caisse_nom", "type_mouvement", "montant",
            "date_mouvement", "motif", "justificatif",
        ]
        read_only_fields = ["id", "date_mouvement"]
