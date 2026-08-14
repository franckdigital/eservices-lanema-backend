from rest_framework import serializers

from .models import Formation, InscriptionParticipant, SessionFormation, SupportPedagogique


class FormationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = [
            "id", "reference", "titre", "type_formation", "modalite", "certifiante",
            "duree_heures", "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class SessionFormationSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="formation.titre", read_only=True)
    formateur_nom = serializers.CharField(source="formateur.user.username", read_only=True, default=None)
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True, default=None)

    class Meta:
        model = SessionFormation
        fields = [
            "id", "formation", "formation_titre", "formateur", "formateur_nom", "entreprise", "entreprise_nom",
            "date_debut", "date_fin_prevue", "date_fin_reelle", "statut", "capacite_max",
            "evaluation_formateur", "evaluation_session", "cout_revient",
        ]
        read_only_fields = ["id"]


class InscriptionParticipantSerializer(serializers.ModelSerializer):
    participant_nom = serializers.CharField(source="participant.__str__", read_only=True)
    participant_email = serializers.CharField(source="participant.email", read_only=True, default=None)
    session_reference = serializers.CharField(source="session.formation.titre", read_only=True)

    class Meta:
        model = InscriptionParticipant
        fields = [
            "id", "session", "session_reference", "participant", "participant_nom", "participant_email",
            "present", "reussite", "certifie", "abandon",
            # Fiche de satisfaction : renseignée par le participant via son lien
            # public (token), lecture seule ici — le staff consulte, ne modifie pas.
            "token", "note_formateur", "note_session", "commentaire", "date_evaluation",
        ]
        read_only_fields = ["id", "token", "note_formateur", "note_session", "commentaire", "date_evaluation"]


class EvaluationSatisfactionDetailSerializer(serializers.ModelSerializer):
    """Vue publique (sans authentification) d'une inscription via son token :
    juste ce qu'il faut pour afficher le formulaire de satisfaction."""
    participant_nom = serializers.CharField(source="participant.__str__", read_only=True)
    formation_titre = serializers.CharField(source="session.formation.titre", read_only=True)
    formateur_nom = serializers.SerializerMethodField()
    date_session = serializers.DateTimeField(source="session.date_debut", read_only=True)
    deja_evalue = serializers.SerializerMethodField()

    class Meta:
        model = InscriptionParticipant
        fields = ["participant_nom", "formation_titre", "formateur_nom", "date_session", "deja_evalue"]

    def get_formateur_nom(self, obj):
        if not obj.session.formateur:
            return None
        user = obj.session.formateur.user
        return user.get_full_name() or user.username

    def get_deja_evalue(self, obj):
        return obj.date_evaluation is not None


class SupportPedagogiqueSerializer(serializers.ModelSerializer):
    formation_titre = serializers.CharField(source="formation.titre", read_only=True, default=None)

    class Meta:
        model = SupportPedagogique
        fields = [
            "id", "formation", "formation_titre", "titre", "type_contenu",
            "date_creation", "date_derniere_maj", "nombre_telechargements",
        ]
        read_only_fields = ["id", "date_creation"]
