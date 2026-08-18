from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    FicheAgent, MissionRH, EvaluationRH, FormationRH,
    InscriptionFormationRH, DocumentRH, Direction, Service, SousDirection,
    DemandeAttestation
)


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class FicheAgentSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    service_nom = serializers.CharField(source='service.nom', read_only=True)
    sous_direction_nom = serializers.CharField(source='sous_direction.nom', read_only=True)
    user_info = UserBriefSerializer(source='user', read_only=True)
    photo_url = serializers.SerializerMethodField()
    anciennete = serializers.SerializerMethodField()
    presence_aujourdhui = serializers.SerializerMethodField()

    class Meta:
        model = FicheAgent
        fields = '__all__'

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
        return None

    def get_presence_aujourdhui(self, obj):
        """Etat du pointage du jour pour cette fiche, tous canaux confondus
        (assiste via fiche_agent, ou auto-pointage via l'Agent lie) — utilise
        par l'ecran mobile "pointage-agents" pour activer/griser les boutons
        Arrivee/Depart selon ce qui a deja ete enregistre aujourd'hui."""
        from django.db.models import Q
        from django.utils import timezone
        from .models import Presence

        today = timezone.now().date()
        query = Q(fiche_agent=obj)
        if obj.user_id:
            query |= Q(agent__user_id=obj.user_id)
        presence = Presence.objects.filter(query, date_presence=today).order_by('-updated_at').first()
        if not presence:
            return None
        return {
            'heure_arrivee': presence.heure_arrivee.strftime('%H:%M:%S') if presence.heure_arrivee else None,
            'heure_depart': presence.heure_depart.strftime('%H:%M:%S') if presence.heure_depart else None,
            'statut': presence.statut,
        }

    def get_anciennete(self, obj):
        if obj.date_prise_service:
            from datetime import date
            delta = date.today() - obj.date_prise_service
            years = delta.days // 365
            months = (delta.days % 365) // 30
            return {'annees': years, 'mois': months}
        return None


class MissionRHSerializer(serializers.ModelSerializer):
    agent_info = UserBriefSerializer(source='agent', read_only=True)
    valideur_info = UserBriefSerializer(source='valideur', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    duree_jours = serializers.SerializerMethodField()

    class Meta:
        model = MissionRH
        fields = '__all__'

    def get_duree_jours(self, obj):
        if obj.date_debut and obj.date_fin:
            return (obj.date_fin - obj.date_debut).days + 1
        return 0


class EvaluationRHSerializer(serializers.ModelSerializer):
    agent_info = UserBriefSerializer(source='agent', read_only=True)
    evaluateur_info = UserBriefSerializer(source='evaluateur', read_only=True)
    mention_display = serializers.CharField(source='get_mention_display', read_only=True)

    class Meta:
        model = EvaluationRH
        fields = '__all__'


class FormationRHSerializer(serializers.ModelSerializer):
    inscrits_count = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    created_by_info = UserBriefSerializer(source='created_by', read_only=True)

    class Meta:
        model = FormationRH
        fields = '__all__'

    def get_inscrits_count(self, obj):
        return obj.inscriptions.count()


class InscriptionFormationRHSerializer(serializers.ModelSerializer):
    agent_info = UserBriefSerializer(source='agent', read_only=True)
    formation_info = FormationRHSerializer(source='formation', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = InscriptionFormationRH
        fields = '__all__'


class DocumentRHSerializer(serializers.ModelSerializer):
    agent_info = UserBriefSerializer(source='agent', read_only=True)
    type_display = serializers.CharField(source='get_type_document_display', read_only=True)
    fichier_url = serializers.SerializerMethodField()
    created_by_info = UserBriefSerializer(source='created_by', read_only=True)

    class Meta:
        model = DocumentRH
        fields = '__all__'

    def get_fichier_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
        return None


class DemandeAttestationSerializer(serializers.ModelSerializer):
    agent_info = UserBriefSerializer(source='agent', read_only=True)
    responsable_info = UserBriefSerializer(source='responsable_rh', read_only=True)
    type_display = serializers.CharField(source='get_type_attestation_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = DemandeAttestation
        fields = '__all__'
        read_only_fields = ['numero_attestation', 'created_at', 'updated_at', 'pdf_file']

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
        return None
