from collections import Counter

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from dfir_participants.models import ParticipantDFIR
from core.direction_access import direction_permission, scope_queryset_to_owner, user_tier

from .models import Formation, InscriptionParticipant, SessionFormation, SupportPedagogique
from .serializers import (
    EvaluationSatisfactionDetailSerializer,
    FormationSerializer,
    InscriptionParticipantSerializer,
    SessionFormationSerializer,
    SupportPedagogiqueSerializer,
)

# Page "Formations" (Sessions + Inscriptions) : seule page opérationnelle
# accessible au palier "terrain" (formateur) — mais un formateur ne voit/
# modifie que ses propres sessions (et les inscriptions qui s'y rattachent).
# Le catalogue (Formation) et les Supports pédagogiques restent réservés à
# l'encadrement (page Catalogue séparée côté frontend).
DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_formations_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI Formations (categorie 1) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    formations = Formation.objects.all()
    if date_debut and date_fin:
        formations = formations.filter(date_creation__date__range=(date_debut, date_fin))

    sessions = SessionFormation.objects.all()
    if date_debut and date_fin:
        sessions = sessions.filter(date_debut__date__range=(date_debut, date_fin))

    sessions_planifiees_total = sessions.exclude(statut="ANNULEE").count()
    sessions_terminees = sessions.filter(statut="TERMINEE").count()
    taux_realisation_plan = (
        round(sessions_terminees / sessions_planifiees_total * 100, 1) if sessions_planifiees_total else None
    )

    return {
        "nombre_formations_organisees": formations.count(),
        "nombre_sessions_realisees": sessions_terminees,
        "nombre_formations_inter_entreprises": formations.filter(type_formation="INTER_ENTREPRISE").count(),
        "nombre_formations_intra_entreprises": formations.filter(type_formation="INTRA_ENTREPRISE").count(),
        "nombre_formations_sur_mesure": formations.filter(type_formation="SUR_MESURE").count(),
        "nombre_formations_certifiantes": formations.filter(certifiante=True).count(),
        "nombre_formations_en_ligne": formations.filter(modalite="EN_LIGNE").count(),
        "nombre_formations_presentielles": formations.filter(modalite="PRESENTIEL").count(),
        "nombre_formations_hybrides": formations.filter(modalite="HYBRIDE").count(),
        "taux_realisation_plan_annuel": taux_realisation_plan,
    }


def compute_participants_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI Participants (categorie 2) de la DFIR."""
    inscriptions = InscriptionParticipant.objects.select_related(
        "participant__entreprise", "session__entreprise"
    )
    if date_debut and date_fin:
        inscriptions = inscriptions.filter(session__date_debut__date__range=(date_debut, date_fin))

    total_inscriptions = inscriptions.count()
    participants_ids = set(inscriptions.values_list("participant_id", flat=True))

    entreprises_ids = set()
    for insc in inscriptions:
        if insc.session.entreprise_id:
            entreprises_ids.add(insc.session.entreprise_id)
        elif insc.participant.entreprise_id:
            entreprises_ids.add(insc.participant.entreprise_id)

    nouveaux_participants = ParticipantDFIR.objects.all()
    if date_debut and date_fin:
        nouveaux_participants = nouveaux_participants.filter(created_at__date__range=(date_debut, date_fin))

    evalues_reussite = inscriptions.filter(reussite__isnull=False)
    taux_reussite = (
        round(evalues_reussite.filter(reussite=True).count() / evalues_reussite.count() * 100, 1)
        if evalues_reussite.count() else None
    )

    evalues_presence = inscriptions.filter(present__isnull=False)
    taux_assiduite = (
        round(evalues_presence.filter(present=True).count() / evalues_presence.count() * 100, 1)
        if evalues_presence.count() else None
    )

    taux_abandon = (
        round(inscriptions.filter(abandon=True).count() / total_inscriptions * 100, 1) if total_inscriptions else None
    )

    sessions_periode = SessionFormation.objects.all()
    if date_debut and date_fin:
        sessions_periode = sessions_periode.filter(date_debut__date__range=(date_debut, date_fin))
    satisfaction_moyenne = sessions_periode.filter(evaluation_session__isnull=False).aggregate(
        m=Avg("evaluation_session")
    )["m"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    nb_sessions = sessions_periode.count()
    moyenne_participants_session = round(total_inscriptions / nb_sessions, 1) if nb_sessions else None

    counts_par_entreprise = Counter()
    for insc in inscriptions:
        entreprise_id = insc.session.entreprise_id or insc.participant.entreprise_id
        if entreprise_id:
            counts_par_entreprise[entreprise_id] += 1
    nb_entreprises_fideles = sum(1 for c in counts_par_entreprise.values() if c > 1)
    taux_fidelisation = (
        round(nb_entreprises_fideles / len(entreprises_ids) * 100, 1) if entreprises_ids else None
    )

    return {
        "nombre_total_participants": len(participants_ids),
        "nombre_nouveaux_participants": nouveaux_participants.count(),
        "nombre_entreprises_formees": len(entreprises_ids),
        "nombre_participants_certifies": inscriptions.filter(certifie=True).count(),
        "taux_reussite_evaluations": taux_reussite,
        "taux_assiduite": taux_assiduite,
        "taux_abandon": taux_abandon,
        "taux_satisfaction_apprenants": taux_satisfaction,
        "nombre_moyen_participants_par_session": moyenne_participants_session,
        "taux_fidelisation_entreprises": taux_fidelisation,
    }


def compute_ressources_pedagogiques_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Ressources pedagogiques (categorie 9) de la DFIR."""
    supports = SupportPedagogique.objects.all()
    if date_debut and date_fin:
        supports = supports.filter(date_creation__date__range=(date_debut, date_fin))

    total_supports = supports.count()
    taux_maj = (
        round(supports.filter(date_derniere_maj__isnull=False).count() / total_supports * 100, 1)
        if total_supports else None
    )

    sessions_elearning = SessionFormation.objects.filter(formation__modalite__in=["EN_LIGNE", "HYBRIDE"])
    if date_debut and date_fin:
        sessions_elearning = sessions_elearning.filter(date_debut__date__range=(date_debut, date_fin))
    inscriptions_elearning = InscriptionParticipant.objects.filter(session__in=sessions_elearning)
    total_elearning = inscriptions_elearning.count()
    taux_utilisation = (
        round(inscriptions_elearning.filter(present=True).count() / total_elearning * 100, 1)
        if total_elearning else None
    )

    return {
        "nombre_supports_crees": total_supports,
        "nombre_modules_disponibles": Formation.objects.count(),
        "nombre_contenus_numeriques_produits": supports.filter(type_contenu__in=["VIDEO", "QUIZ"]).count(),
        "taux_mise_a_jour_contenus": taux_maj,
        "nombre_telechargements_ressources": supports.aggregate(t=Sum("nombre_telechargements"))["t"] or 0,
        "taux_utilisation_plateforme_elearning": taux_utilisation,
    }


class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    serializer_class = FormationSerializer
    permission_classes = [DFIR_ENCADREMENT]


class SessionFormationViewSet(viewsets.ModelViewSet):
    queryset = SessionFormation.objects.select_related("formation", "formateur__user", "entreprise").all()
    serializer_class = SessionFormationSerializer
    permission_classes = [DFIR_MEMBRE]

    def get_queryset(self):
        return scope_queryset_to_owner(super().get_queryset(), self.request, "formateur__user")

    def perform_create(self, serializer):
        if user_tier(self.request.user) == 'terrain' and not serializer.validated_data.get('formateur'):
            from dfir_formateurs.models import FormateurDFIR
            formateur = FormateurDFIR.objects.filter(user=self.request.user).first()
            if formateur:
                serializer.save(formateur=formateur)
                return
        serializer.save()


class InscriptionParticipantViewSet(viewsets.ModelViewSet):
    queryset = InscriptionParticipant.objects.select_related("session__formation", "participant").all()
    serializer_class = InscriptionParticipantSerializer
    permission_classes = [DFIR_MEMBRE]

    def get_queryset(self):
        return scope_queryset_to_owner(super().get_queryset(), self.request, "session__formateur__user")

    @action(detail=True, methods=["post"], url_path="envoyer-satisfaction")
    def envoyer_satisfaction(self, request, pk=None):
        """Le formateur/l'encadrement clique un bouton pour envoyer par email
        le lien de la fiche de satisfaction au participant (déjà enregistré
        dans le système, cf. ParticipantDFIR.email)."""
        inscription = self.get_object()
        email = (inscription.participant.email or "").strip()
        if not email:
            return Response({"detail": "Ce participant n'a pas d'email enregistré."}, status=400)
        if inscription.date_evaluation is not None:
            return Response({"detail": "Ce participant a déjà soumis son évaluation."}, status=400)

        lien = f"{getattr(settings, 'FRONTEND_BASE_URL', '')}/dfir/satisfaction/{inscription.token}"
        formation_titre = inscription.session.formation.titre
        send_mail(
            subject=f"Votre avis sur la formation « {formation_titre} »",
            message=(
                f"Bonjour {inscription.participant.prenom or ''},\n\n"
                f"Merci d'avoir participé à la formation « {formation_titre} ».\n"
                "Votre avis nous aide à améliorer nos formations : merci de prendre une minute "
                "pour évaluer la formation et le formateur.\n\n"
                f"Lien vers la fiche de satisfaction : {lien}\n\n"
                "Merci pour votre confiance,\nLa Direction Formation, Innovation et Recherche — LANEMA"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=True,
        )
        return Response({"detail": f"Lien envoyé à {email}."})


class EvaluationSatisfactionView(APIView):
    """Fiche de satisfaction publique : accessible via un lien unique (token)
    envoyé au participant après sa session, sans compte ni connexion.
    GET  : affiche le contexte (formation, formateur, déjà évalué ou non).
    POST : enregistre les notes (une seule fois par token)."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_object(self, token):
        return InscriptionParticipant.objects.select_related(
            "session__formation", "session__formateur__user", "participant"
        ).get(token=token)

    def get(self, request, token):
        try:
            inscription = self.get_object(token)
        except InscriptionParticipant.DoesNotExist:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EvaluationSatisfactionDetailSerializer(inscription).data)

    def post(self, request, token):
        try:
            inscription = self.get_object(token)
        except InscriptionParticipant.DoesNotExist:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_404_NOT_FOUND)

        if inscription.date_evaluation is not None:
            return Response({"detail": "Cette évaluation a déjà été soumise."}, status=status.HTTP_400_BAD_REQUEST)

        note_formateur = request.data.get("note_formateur")
        note_session = request.data.get("note_session")
        try:
            note_formateur = int(note_formateur)
            note_session = int(note_session)
        except (TypeError, ValueError):
            return Response({"detail": "Merci de renseigner les deux notes (sur 5)."}, status=status.HTTP_400_BAD_REQUEST)
        if not (1 <= note_formateur <= 5) or not (1 <= note_session <= 5):
            return Response({"detail": "Les notes doivent être comprises entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)

        inscription.note_formateur = note_formateur
        inscription.note_session = note_session
        inscription.commentaire = (request.data.get("commentaire") or "")[:2000]
        inscription.date_evaluation = timezone.now()
        inscription.save(update_fields=["note_formateur", "note_session", "commentaire", "date_evaluation"])
        return Response({"detail": "Merci pour votre évaluation."})


class SupportPedagogiqueViewSet(viewsets.ModelViewSet):
    queryset = SupportPedagogique.objects.select_related("formation").all()
    serializer_class = SupportPedagogiqueSerializer
    permission_classes = [DFIR_ENCADREMENT]


class FormationsKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_formations_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class ParticipantsKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_participants_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class RessourcesPedagogiquesKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_ressources_pedagogiques_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
