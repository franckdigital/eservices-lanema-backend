from rest_framework import serializers

from dfir_email.crypto import encrypt_value

from .models import BonCommande, CompteEmailLabo, EmailDevis, Facture, Proforma, DemandeAnalyse


class ProformaSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    valide_par_responsable_nom = serializers.CharField(
        source="valide_par_responsable.get_full_name", read_only=True, default=None
    )
    client_nom = serializers.SerializerMethodField(read_only=True)
    client_telephone = serializers.CharField(source="client.client_profile.telephone", read_only=True, default="")
    objet = serializers.CharField(source="demande_devis.objet", read_only=True, default="")
    type_analyse = serializers.CharField(source="demande_devis.type_analyse", read_only=True, default="")
    accord_sous_traitance = serializers.BooleanField(source="demande_devis.accord_sous_traitance", read_only=True, default=False)
    montant_tva = serializers.SerializerMethodField(read_only=True)
    date_validite = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proforma
        fields = [
            "id",
            "numero",
            "client",
            "demande_devis",
            "client_email",
            "client_nom",
            "client_telephone",
            "objet",
            "type_analyse",
            "accord_sous_traitance",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "devise",
            "statut",
            "date_emission",
            "date_validite",
            "valide_par_responsable",
            "valide_par_responsable_nom",
            "date_validation_responsable",
            "signature_responsable_appliquee",
            "remise",
            "envoye_le",
            "canal_envoi",
            "lu_approuve",
            "lu_approuve_le",
        ]
        read_only_fields = [
            "id", "date_emission", "demande_devis",
            "valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee",
            "remise", "envoye_le", "canal_envoi", "lu_approuve", "lu_approuve_le",
        ]


    def get_montant_tva(self, obj):
        return (obj.montant_ttc or 0) - (obj.montant_ht or 0)

    def get_date_validite(self, obj):
        # Validite de l'offre : 30 jours a compter de l'emission
        from datetime import timedelta
        return (obj.date_emission + timedelta(days=30)) if obj.date_emission else None

    def get_client_nom(self, obj):
        profil = getattr(obj.client, "client_profile", None)
        return (getattr(profil, "raison_sociale", "") or obj.client.get_full_name() or obj.client.username)


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
            "travaux_autorises",
            "travaux_autorises_le",
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
    bon_commande_signe = serializers.SerializerMethodField(read_only=True)
    code_client = serializers.CharField(source="client.client_profile.code_client", read_only=True, default=None)
    objet = serializers.CharField(source="demande_devis.objet", read_only=True, default=None)
    type_analyse = serializers.CharField(source="demande_devis.type_analyse", read_only=True, default=None)
    echantillons_prevus = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DemandeAnalyse
        fields = [
            "id",
            "numero",
            "client",
            "code_client",
            "demande_devis",
            "objet",
            "type_analyse",
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
            "bon_commande_signe",
            "echantillons_prevus",
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

    def get_bon_commande_signe(self, obj):
        return bool(obj.facture and obj.facture.bon_commande_id and obj.facture.bon_commande.statut == "SIGNE_CLIENT")

    def get_echantillons_prevus(self, obj):
        if obj.demande_devis_id is None:
            return []
        return [
            {"id": e.id, "nom": e.nom, "quantite": e.quantite}
            for e in obj.demande_devis.echantillons_prevus.all()
        ]


class CompteEmailLaboSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, required=False, allow_blank=True)
    a_mot_de_passe = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompteEmailLabo
        fields = [
            "id", "nom_affichage", "adresse_email", "serveur_sortant", "port_sortant", "ssl_sortant",
            "identifiant", "mot_de_passe", "a_mot_de_passe", "signature", "est_principal", "actif", "created_at",
        ]
        read_only_fields = ["id", "created_at", "a_mot_de_passe"]

    def get_a_mot_de_passe(self, obj):
        return bool(obj.mot_de_passe)

    def create(self, validated_data):
        mdp = validated_data.pop("mot_de_passe", "")
        validated_data["mot_de_passe"] = encrypt_value(mdp)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        mdp = validated_data.pop("mot_de_passe", None)
        if mdp:  # champ vide = conserver le mot de passe actuel
            validated_data["mot_de_passe"] = encrypt_value(mdp)
        return super().update(instance, validated_data)


class EmailDevisSerializer(serializers.ModelSerializer):
    envoye_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailDevis
        fields = [
            "id", "canal", "envoye_par_nom", "destinataires", "destinataires_cc", "sujet",
            "pdf_joint", "nb_pieces_jointes", "statut", "erreur", "created_at",
        ]

    def get_envoye_par_nom(self, obj):
        u = obj.envoye_par
        return (u.get_full_name() or u.username) if u else None
