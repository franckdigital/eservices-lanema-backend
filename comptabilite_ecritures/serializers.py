from rest_framework import serializers

from .models import CompteComptable, EcritureComptable, JournalComptable


class CompteComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteComptable
        fields = ["id", "numero", "intitule", "type_compte"]
        read_only_fields = ["id"]


class JournalComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalComptable
        fields = ["id", "code", "libelle"]
        read_only_fields = ["id"]


class EcritureComptableSerializer(serializers.ModelSerializer):
    journal_code = serializers.CharField(source="journal.code", read_only=True)
    compte_debit_numero = serializers.CharField(source="compte_debit.numero", read_only=True)
    compte_credit_numero = serializers.CharField(source="compte_credit.numero", read_only=True)
    piece_numero = serializers.CharField(source="piece.numero", read_only=True, default=None)

    class Meta:
        model = EcritureComptable
        fields = [
            "id", "numero", "journal", "journal_code", "date_ecriture",
            "compte_debit", "compte_debit_numero", "compte_credit", "compte_credit_numero",
            "montant", "libelle", "piece", "piece_numero", "valide",
        ]
        read_only_fields = ["id", "date_ecriture"]
