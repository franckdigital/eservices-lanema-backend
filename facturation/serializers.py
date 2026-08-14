from rest_framework import serializers

from .models import BonCommande, Facture, Proforma, DemandeAnalyse


class ProformaSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    valide_par_responsable_nom = serializers.CharField(
        source="valide_par_responsable.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Proforma
        fields = [
            "id",
            "numero",
            "client",
            "demande_devis",
            "client_email",
            "montant_ht",
            "montant_ttc",
            "devise",
            "statut",
            "date_emission",
            "valide_par_responsable",
            "valide_par_responsable_nom",
            "date_validation_responsable",
            "signature_responsable_appliquee",
        ]
        read_only_fields = [
            "id", "date_emission", "demande_devis",
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
        ]


class BonCommandeSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    proforma_numero = serializers.CharField(source="proforma.numero", read_only=True)
    valide_par_responsable_nom = serializers.CharField(
        source="valide_par_responsable.get_full_name", read_only=True, default=None
    )
    signature_client_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BonCommande
        fields = [
            "id",
            "numero",
            "client",
            "client_email",
            "proforma",
            "proforma_numero",
            "montant_ht",
            "montant_ttc",
            "devise",
            "statut",
            "date_emission",
            "signature_client_image",
            "signature_client_image_url",
            "date_signature_client",
            "valide_par_responsable",
            "valide_par_responsable_nom",
            "date_validation_responsable",
            "signature_responsable_appliquee",
        ]
        read_only_fields = [
            "id", "numero", "client", "proforma", "montant_ht", "montant_ttc", "devise",
            "date_emission", "date_signature_client",
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
        ]

    def get_signature_client_image_url(self, obj):  # pragma: no cover - simple helper
        request = self.context.get("request")
        if obj.signature_client_image and request is not None:
            return request.build_absolute_uri(obj.signature_client_image.url)
        if obj.signature_client_image:
            return obj.signature_client_image.url
        return None


class FactureSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    proforma_numero = serializers.CharField(source="proforma.numero", read_only=True, default=None)
    bon_commande_numero = serializers.CharField(source="bon_commande.numero", read_only=True, default=None)
    valide_par_responsable_nom = serializers.CharField(
        source="valide_par_responsable.get_full_name", read_only=True, default=None
    )

    justificatif_paiement_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Facture
        fields = [
            "id",
            "numero",
            "client",
            "client_email",
            "proforma",
            "proforma_numero",
            "bon_commande",
            "bon_commande_numero",
            "montant_ht",
            "montant_ttc",
            "devise",
            "statut",
            "date_emission",
            "date_echeance",
            "date_paiement",
            "mode_paiement",
            "justificatif_paiement",
            "justificatif_paiement_url",
            "paiement_valide",
            "visible_client",
            "reference_paiement",
            "valide_par_responsable",
            "valide_par_responsable_nom",
            "date_validation_responsable",
            "signature_responsable_appliquee",
        ]
        read_only_fields = [
            "id",
            "date_emission",
            "date_paiement",
            "paiement_valide",
            "visible_client",
            "proforma",
            "bon_commande",
            "valide_par_responsable",
            "date_validation_responsable",
            "signature_responsable_appliquee",
        ]

    def get_justificatif_paiement_url(self, obj):  # pragma: no cover - simple helper
        request = self.context.get("request")
        if obj.justificatif_paiement and request is not None:
            return request.build_absolute_uri(obj.justificatif_paiement.url)
        if obj.justificatif_paiement:
            return obj.justificatif_paiement.url
        return None


class DemandeAnalyseSerializer(serializers.ModelSerializer):
    demande_devis_numero = serializers.CharField(source="demande_devis.numero", read_only=True)
    proforma_acceptee_numero = serializers.CharField(source="proforma.numero", read_only=True)
    facture_numero = serializers.CharField(source="facture.numero", read_only=True, default=None)
    laboratoire_nom = serializers.CharField(source="laboratoire.nom", read_only=True, default=None)
    paiement_effectue = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DemandeAnalyse
        fields = [
            "id",
            "numero",
            "client",
            "demande_devis",
            "proforma",
            "facture",
            "facture_numero",
            "laboratoire",
            "laboratoire_nom",
            "demande_devis_numero",
            "proforma_acceptee_numero",
            "statut",
            "montant_ht",
            "montant_ttc",
            "date_creation",
            "date_depot_echantillons",
            "date_debut_analyse",
            "date_fin_analyse",
            "observations",
            "paiement_effectue",
        ]
        read_only_fields = [
            "id",
            "numero",
            "client",
            "demande_devis",
            "proforma",
            "facture",
            "date_creation",
        ]

    def get_paiement_effectue(self, obj):
        # La facture est desormais directement rattachee a la demande d'analyse
        # (chainage explicite), plus besoin d'heuristique client+montant.
        return obj.facture is not None and obj.facture.statut == "PAYEE"
