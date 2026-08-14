from rest_framework import serializers

from .crypto import encrypt_value
from .models import CompteEmailDFIR, EmailDFIR, PieceJointeEmailDFIR
from .services import detect_provider_config


class CompteEmailDFIRSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, required=False, allow_blank=True)
    config_detectee = serializers.SerializerMethodField()

    class Meta:
        model = CompteEmailDFIR
        fields = [
            "id", "type_compte", "nom_affichage", "adresse_email", "identifiant", "mot_de_passe",
            "serveur_entrant", "port_entrant", "ssl_entrant",
            "serveur_sortant", "port_sortant", "ssl_sortant",
            "est_principal", "statut", "derniere_synchro", "derniere_erreur", "created_at",
            "config_detectee",
        ]
        read_only_fields = ["id", "statut", "derniere_synchro", "derniere_erreur", "created_at"]

    def get_config_detectee(self, obj):
        return detect_provider_config(obj.adresse_email)

    def create(self, validated_data):
        validated_data["utilisateur"] = self.context["request"].user
        if validated_data.get("mot_de_passe"):
            validated_data["mot_de_passe"] = encrypt_value(validated_data["mot_de_passe"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("mot_de_passe"):
            validated_data["mot_de_passe"] = encrypt_value(validated_data["mot_de_passe"])
        else:
            # Champ vide à la modification = on ne touche pas au mot de passe existant.
            validated_data.pop("mot_de_passe", None)
        return super().update(instance, validated_data)


class PieceJointeEmailDFIRSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceJointeEmailDFIR
        fields = ["id", "nom_fichier", "fichier", "type_mime", "taille"]
        read_only_fields = ["id", "taille"]


class EmailDFIRSerializer(serializers.ModelSerializer):
    pieces_jointes = PieceJointeEmailDFIRSerializer(many=True, read_only=True)
    compte_email = serializers.CharField(source="compte.adresse_email", read_only=True)
    en_reponse_a_sujet = serializers.CharField(source="en_reponse_a.sujet", read_only=True, default=None)

    class Meta:
        model = EmailDFIR
        fields = [
            "id", "compte", "compte_email", "direction", "message_id", "thread_id",
            "en_reponse_a", "en_reponse_a_sujet", "sujet", "expediteur_nom", "expediteur_email",
            "destinataires", "destinataires_cc", "corps_texte", "corps_html", "date_message",
            "statut", "priorite", "score_urgence", "resume_ia", "actions_detectees", "traite_par_ia",
            "pieces_jointes", "created_at",
        ]
        read_only_fields = [
            "id", "message_id", "thread_id", "direction", "date_message", "score_urgence",
            "resume_ia", "actions_detectees", "traite_par_ia", "pieces_jointes", "created_at",
        ]


class EmailDFIRListSerializer(serializers.ModelSerializer):
    """Version allégée pour la liste (boîte de réception) — sans le corps complet."""
    compte_email = serializers.CharField(source="compte.adresse_email", read_only=True)
    nombre_pieces_jointes = serializers.IntegerField(source="pieces_jointes.count", read_only=True)

    class Meta:
        model = EmailDFIR
        fields = [
            "id", "compte", "compte_email", "direction", "thread_id", "sujet",
            "expediteur_nom", "expediteur_email", "destinataires", "date_message",
            "statut", "priorite", "score_urgence", "traite_par_ia", "nombre_pieces_jointes", "created_at",
        ]
