from rest_framework import serializers

from .models import ActionQualite, Audit, Echantillon, Essai, NonConformite, RecommandationAudit


class EchantillonSerializer(serializers.ModelSerializer):
    demande_numero = serializers.CharField(source='demande.numero', read_only=True)

    class Meta:
        model = Echantillon
        fields = [
            "id",
            "code_echantillon",
            "designation",
            "type_echantillon",
            "demande",
            "demande_numero",
            "quantite",
            "statut",
            "conforme",
            "date_reception",
            "emplacement_stockage",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "code_echantillon", "created_at", "updated_at"]


class NonConformiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = NonConformite
        fields = [
            "id",
            "numero",
            "type_nc",
            "gravite",
            "description",
            "responsable",
            "essai",
            "date_creation",
        ]
        read_only_fields = ["id", "numero", "date_creation"]


class ActionQualiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionQualite
        fields = [
            "id", "non_conformite", "type", "description", "responsable",
            "statut", "date_planification", "date_cloture",
        ]
        read_only_fields = ["id", "date_planification"]


class RecommandationAuditSerializer(serializers.ModelSerializer):
    audit_reference = serializers.CharField(source="audit.reference", read_only=True)

    class Meta:
        model = RecommandationAudit
        fields = ["id", "audit", "audit_reference", "description", "appliquee", "date_echeance"]
        read_only_fields = ["id"]


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = [
            "id",
            "reference",
            "type_audit",
            "organisme",
            "date_audit",
            "resultat",
        ]
        read_only_fields = ["id"]


class EssaiSerializer(serializers.ModelSerializer):
    echantillon_code = serializers.CharField(source='echantillon.code_echantillon', read_only=True)
    echantillon_id = serializers.PrimaryKeyRelatedField(
        source='echantillon',
        queryset=Echantillon.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    laboratoire_nom = serializers.CharField(source='laboratoire.nom', read_only=True, default=None)
    technicien_user_nom = serializers.CharField(source='technicien_user.username', read_only=True, default=None)

    class Meta:
        model = Essai
        fields = [
            "id",
            "numero",
            "type_essai",
            "echantillon",
            "echantillon_id",
            "echantillon_code",
            "laboratoire",
            "laboratoire_nom",
            "statut",
            "date_debut",
            "date_fin_prevue",
            "date_fin",
            "technicien",
            "technicien_user",
            "technicien_user_nom",
            "urgent",
            "est_reprise",
            "essai_origine",
            "erreur_detectee",
            "cout_revient",
            "norme",
            "observations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "numero", "created_at", "updated_at"]
