from rest_framework import serializers

from .models import Budget, Depense, EcritureComptable, Recette


class BudgetSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True, default=None)
    taux_execution = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            "id", "direction", "direction_nom", "annee", "categorie", "montant_prevu",
            "montant_engage", "montant_realise", "nombre_revisions", "date_derniere_revision",
            "taux_execution", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_taux_execution(self, obj):
        if not obj.montant_prevu:
            return None
        return round(float(obj.montant_realise) / float(obj.montant_prevu) * 100, 1)


class EcritureComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcritureComptable
        fields = ["id", "reference", "date_ecriture", "montant", "type", "piece_justificative", "erreur", "created_at"]
        read_only_fields = ["id", "reference", "created_at"]


class RecetteSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True, default=None)

    class Meta:
        model = Recette
        fields = [
            "id", "reference", "direction", "direction_nom", "type_prestation", "client_nom",
            "montant", "date_emission", "date_encaissement", "statut",
        ]
        read_only_fields = ["id", "reference"]


class DepenseSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True, default=None)
    site_nom = serializers.CharField(source="site.nom", read_only=True, default=None)

    class Meta:
        model = Depense
        fields = [
            "id", "reference", "direction", "direction_nom", "site", "site_nom", "categorie",
            "prestation_associee", "fournisseur_nom", "montant", "date_engagement",
            "date_paiement", "statut",
        ]
        read_only_fields = ["id", "reference"]
