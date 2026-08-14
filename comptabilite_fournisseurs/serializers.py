from rest_framework import serializers

from .models import FactureFournisseur, FournisseurComptable, PaiementFournisseur


class FournisseurComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = FournisseurComptable
        fields = [
            "id", "raison_sociale", "rccm", "adresse", "telephone", "email",
            "rib", "contact_nom", "actif", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class FactureFournisseurSerializer(serializers.ModelSerializer):
    fournisseur_nom = serializers.CharField(source="fournisseur.raison_sociale", read_only=True)

    class Meta:
        model = FactureFournisseur
        fields = [
            "id", "reference", "fournisseur", "fournisseur_nom", "objet",
            "montant_ht", "montant_ttc", "date_reception", "date_echeance",
            "statut", "piece_jointe",
        ]
        read_only_fields = ["id", "date_reception"]


class PaiementFournisseurSerializer(serializers.ModelSerializer):
    facture_reference = serializers.CharField(source="facture_fournisseur.reference", read_only=True)

    class Meta:
        model = PaiementFournisseur
        fields = [
            "id", "facture_fournisseur", "facture_reference", "montant",
            "date_paiement", "mode_paiement", "reference_paiement",
        ]
        read_only_fields = ["id", "date_paiement"]
