from rest_framework import serializers

from .models import CertificatFormation, ClasseVirtuelle, Lecon, ProgressionLecon


# ── Gestion (staff, encadrement DFIR) ──────────────────────────────────────

class LeconSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="formation.titre", read_only=True)

    class Meta:
        model = Lecon
        fields = [
            "id", "formation", "formation_titre", "titre", "description", "type_contenu",
            "url_contenu", "texte_contenu", "ordre", "duree_minutes", "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class ClasseVirtuelleSerializer(serializers.ModelSerializer):
    session_reference = serializers.CharField(source="session.formation.titre", read_only=True)

    class Meta:
        model = ClasseVirtuelle
        fields = [
            "id", "session", "session_reference", "titre", "provider",
            "date_debut", "date_fin", "join_url", "compte_rendu", "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class CertificatFormationSerializer(serializers.ModelSerializer):
    participant_nom = serializers.CharField(source="inscription.participant.__str__", read_only=True)
    formation_titre = serializers.CharField(source="inscription.session.formation.titre", read_only=True)

    class Meta:
        model = CertificatFormation
        fields = [
            "id", "inscription", "participant_nom", "formation_titre",
            "numero", "code_verification", "date_delivrance",
        ]
        read_only_fields = ["id", "numero", "code_verification", "date_delivrance"]


# ── "Mon espace" (participant authentifié) ─────────────────────────────────

class ProgressionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressionLecon
        fields = ["vu", "date_vu", "note_personnelle"]


class LeconParticipantSerializer(serializers.ModelSerializer):
    ma_progression = serializers.SerializerMethodField()

    class Meta:
        model = Lecon
        fields = [
            "id", "titre", "description", "type_contenu", "url_contenu",
            "texte_contenu", "ordre", "duree_minutes", "ma_progression",
        ]

    def get_ma_progression(self, obj):
        participant = self.context.get("participant")
        if not participant:
            return None
        progression = obj.progressions.filter(participant=participant).first()
        return ProgressionMiniSerializer(progression).data if progression else {
            "vu": False, "date_vu": None, "note_personnelle": "",
        }


class ClasseVirtuelleParticipantSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="session.formation.titre", read_only=True)

    class Meta:
        model = ClasseVirtuelle
        fields = ["id", "titre", "provider", "date_debut", "date_fin", "join_url", "formation_titre"]


class CertificatParticipantSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="inscription.session.formation.titre", read_only=True)

    class Meta:
        model = CertificatFormation
        fields = ["id", "numero", "code_verification", "date_delivrance", "formation_titre"]


class CertificatVerifySerializer(serializers.ModelSerializer):
    """Vue publique (sans authentification) d'un certificat via son code."""
    participant_nom = serializers.CharField(source="inscription.participant.__str__", read_only=True)
    formation_titre = serializers.CharField(source="inscription.session.formation.titre", read_only=True)

    class Meta:
        model = CertificatFormation
        fields = ["numero", "participant_nom", "formation_titre", "date_delivrance"]
