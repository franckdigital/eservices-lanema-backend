from rest_framework import serializers

from .models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE


class NonConformiteDAESerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)
    ordre_travail_reference = serializers.CharField(source="ordre_travail.reference", read_only=True, default=None)
    origine_label = serializers.CharField(source="get_origine_display", read_only=True)

    class Meta:
        model = NonConformiteDAE
        fields = [
            "id", "reference", "origine", "origine_label", "ordre_travail", "ordre_travail_reference", "gravite",
            "description", "cause", "responsable", "responsable_nom", "statut", "date_creation", "date_echeance",
        ]
        # "reference" est auto-generee (NC-DAE-annee-NNNNN). "statut" reste
        # modifiable manuellement (ex: passage a "En cours de traitement"),
        # mais est aussi mis a jour automatiquement vers "Clôturée" des que
        # toutes les actions correctives liees sont elles-memes cloturees
        # (cf. ActionCorrectiveDAEViewSet.changer_statut).
        read_only_fields = ["id", "reference", "date_creation"]


class ActionCorrectiveDAESerializer(serializers.ModelSerializer):
    non_conformite_reference = serializers.CharField(source="non_conformite.reference", read_only=True)
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = ActionCorrectiveDAE
        fields = [
            "id", "non_conformite", "non_conformite_reference", "analyse_cause", "description", "responsable",
            "responsable_nom", "statut", "date_prevue", "date_realisation",
            "verification_efficacite", "efficace", "date_verification",
        ]
        # "statut" (et les champs de verification qui en decoulent) est en
        # lecture seule ici : toute transition doit passer par l'action
        # changer_statut (verrou verification d'efficacite avant cloture).
        read_only_fields = ["id", "statut", "date_realisation", "verification_efficacite", "efficace", "date_verification"]


class AuditQualiteDAESerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditQualiteDAE
        fields = ["id", "reference", "type_audit", "date_audit", "resultat"]
        read_only_fields = ["id", "reference"]
