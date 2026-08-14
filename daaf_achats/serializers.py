from rest_framework import serializers

from .models import BonCommande, DemandeAchat, Fournisseur, Marche


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ["id", "nom", "contact", "actif", "created_at"]
        read_only_fields = ["id", "created_at"]


class DemandeAchatSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source="direction.nom", read_only=True, default=None)
    demandeur_nom = serializers.CharField(source="demandeur.username", read_only=True, default=None)

    class Meta:
        model = DemandeAchat
        fields = [
            "id", "reference", "direction", "direction_nom", "objet", "demandeur", "demandeur_nom",
            "date_demande", "date_traitement", "statut",
        ]
        read_only_fields = ["id", "reference", "date_demande"]


class BonCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonCommande
        fields = [
            "id", "reference", "demande", "fournisseur_nom", "montant", "date_commande",
            "date_livraison_prevue", "date_livraison_reelle", "statut", "conforme", "note_satisfaction",
        ]
        read_only_fields = ["id", "reference", "date_commande"]


class MarcheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marche
        fields = ["id", "reference", "objet", "montant", "date_attribution", "respect_plan", "statut"]
        read_only_fields = ["id"]
