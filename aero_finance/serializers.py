from rest_framework import serializers

from .models import BonCommandeDAE, DevisDAE, FactureDAE


class DevisDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)
    montant_ht = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    montant_ttc = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = DevisDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "client", "client_nom",
            "description", "montant_main_oeuvre", "montant_pieces", "frais_supplementaires", "taux_tva",
            "montant_ht", "montant_ttc", "statut", "date_creation", "date_validite",
        ]
        read_only_fields = ["id", "reference", "date_creation"]


class BonCommandeDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    devis_reference = serializers.CharField(source="devis.reference", read_only=True, default=None)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)

    class Meta:
        model = BonCommandeDAE
        fields = [
            "id", "reference", "devis", "devis_reference", "ordre_travail", "ordre_travail_reference",
            "client", "client_nom", "montant_ttc", "statut", "date_creation", "date_signature",
        ]
        read_only_fields = ["id", "reference", "date_creation"]


class FactureDAESerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)
    bon_commande_reference = serializers.CharField(source="bon_commande.reference", read_only=True, default=None)

    class Meta:
        model = FactureDAE
        fields = [
            "id", "reference", "ordre_travail", "ordre_travail_reference", "bon_commande", "bon_commande_reference",
            "client", "client_nom", "montant_main_oeuvre", "montant_pieces", "frais_supplementaires", "taux_tva",
            "montant_ht", "montant_ttc", "statut", "date_emission", "date_paiement",
        ]
        read_only_fields = ["id", "date_emission", "montant_ht", "montant_ttc"]
