from rest_framework import serializers

from .models import CompteBancaire, MouvementBancaire, RapprochementBancaire


class CompteBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteBancaire
        fields = ["id", "nom_banque", "numero_compte", "intitule", "solde_initial", "actif"]
        read_only_fields = ["id"]


class MouvementBancaireSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source="compte.numero_compte", read_only=True)

    class Meta:
        model = MouvementBancaire
        fields = [
            "id", "compte", "compte_numero", "type_mouvement", "montant",
            "date_mouvement", "libelle", "rapproche",
        ]
        read_only_fields = ["id"]


class RapprochementBancaireSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source="compte.numero_compte", read_only=True)

    class Meta:
        model = RapprochementBancaire
        fields = [
            "id", "compte", "compte_numero", "date_rapprochement",
            "solde_releve", "solde_comptable", "ecart", "valide",
        ]
        read_only_fields = ["id", "date_rapprochement"]
