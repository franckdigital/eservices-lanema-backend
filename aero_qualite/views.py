from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_dashboard.mixins import HistoriqueMixin, log_historique_dae
from aero_maintenance.models import OrdreTravail
from core.direction_access import direction_permission

from .models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE
from .serializers import ActionCorrectiveDAESerializer, AuditQualiteDAESerializer, NonConformiteDAESerializer

DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')
# Encadrement, ou Contrôleur qualité de palier terrain (cf. cahier des
# charges DAE section 29 : le contrôleur qualité gère les non-conformités,
# les actions correctives et valide les contrôles qualité).
DAE_QUALITE = direction_permission('DAE', min_tier='encadrement', feature_key='dae_role_controleur_qualite')

# Workflow de l'action corrective — cf. cahier des charges DAE section 18 :
# Non-conformite -> Analyse cause -> Action corrective -> Realisation ->
# Verification efficacite -> Cloture. Le retour VERIFIEE -> EN_COURS couvre
# le cas ou l'action s'avere non efficace (reprise necessaire).
TRANSITIONS_ACTION = {
    "PLANIFIEE": ["EN_COURS"],
    "EN_COURS": ["REALISEE"],
    "REALISEE": ["VERIFIEE"],
    "VERIFIEE": ["CLOTUREE", "EN_COURS"],
    "CLOTUREE": [],
}


def compute_qualite_kpis(date_debut=None, date_fin=None):
    """Calcule les KPI Qualite de la DAE (categorie 4 + KPI 14-18 du cahier
    des charges section 24 : taux de conformité, taux de reprise, nombre de
    non-conformités, taux de clôture des actions correctives, taux de retour
    en garantie). Reutilisable directement par le tableau de bord DAE."""
    non_conformites = NonConformiteDAE.objects.all()
    if date_debut and date_fin:
        non_conformites = non_conformites.filter(date_creation__range=(date_debut, date_fin))

    actions = ActionCorrectiveDAE.objects.all()
    audits = AuditQualiteDAE.objects.all()
    if date_debut and date_fin:
        audits = audits.filter(date_audit__range=(date_debut, date_fin))

    total_nc = non_conformites.count()
    taux_cloture = (
        round(non_conformites.filter(statut="CLOTUREE").count() / total_nc * 100, 1) if total_nc else None
    )

    total_actions = actions.count()
    taux_cloture_actions_correctives = (
        round(actions.filter(statut="CLOTUREE").count() / total_actions * 100, 1) if total_actions else None
    )

    total_audits = audits.count()
    taux_conformite_procedures = (
        round(audits.filter(resultat="CONFORME").count() / total_audits * 100, 1) if total_audits else None
    )

    # Reprises apres maintenance : approximation documentee — un nouvel ordre de
    # travail est ouvert sur le meme aeronef apres une non-conformite liee a un
    # ordre de travail anterieur. Sert aussi d'approximation au "taux de retour
    # en garantie" (KPI 18), faute de champ dedie sur OrdreTravail/Reclamation.
    nb_reprises = 0
    for nc in non_conformites.filter(ordre_travail__isnull=False).select_related("ordre_travail__aeronef"):
        aeronef = nc.ordre_travail.aeronef
        if OrdreTravail.objects.filter(aeronef=aeronef, date_demande__date__gt=nc.date_creation).exists():
            nb_reprises += 1

    ordres_termines = OrdreTravail.objects.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"])
    if date_debut and date_fin:
        ordres_termines = ordres_termines.filter(date_demande__date__range=(date_debut, date_fin))
    total_termines = ordres_termines.count()
    ordres_sans_nc = ordres_termines.exclude(non_conformites__isnull=False).distinct().count()
    taux_reussite_premier_passage = (
        round(ordres_sans_nc / total_termines * 100, 1) if total_termines else None
    )
    taux_reprise = round(100 - taux_reussite_premier_passage, 1) if taux_reussite_premier_passage is not None else None
    taux_retour_garantie = round(nb_reprises / total_termines * 100, 1) if total_termines else None

    return {
        "nombre_non_conformites": total_nc,
        "nombre_actions_correctives": actions.count(),
        "taux_cloture_non_conformites": taux_cloture,
        "taux_cloture_actions_correctives": taux_cloture_actions_correctives,
        "nombre_audits": total_audits,
        "taux_conformite_procedures": taux_conformite_procedures,
        "nombre_reprises_apres_maintenance": nb_reprises,
        "taux_reussite_premier_passage": taux_reussite_premier_passage,
        "taux_reprise": taux_reprise,
        "taux_retour_garantie": taux_retour_garantie,
    }


class NonConformiteDAEViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = NonConformiteDAE.objects.select_related("ordre_travail", "responsable").all()
    serializer_class = NonConformiteDAESerializer
    permission_classes = [DAE_QUALITE]


class ActionCorrectiveDAEViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = ActionCorrectiveDAE.objects.select_related("non_conformite", "responsable").all()
    serializer_class = ActionCorrectiveDAESerializer
    permission_classes = [DAE_QUALITE]

    def perform_update(self, serializer):
        """Cf. cahier des charges DAE section 28 — declencheur "action
        corrective" : notifie le responsable nouvellement affecte."""
        ancien_responsable_id = self.get_object().responsable_id
        instance = serializer.save()
        if instance.responsable_id and instance.responsable_id != ancien_responsable_id:
            from core.models import Notification

            Notification.objects.create(
                user_id=instance.responsable_id, type_notif="rappel",
                contenu=f"Action corrective assignée : {instance.non_conformite.reference} — {instance.description[:80]}",
                lien="/dae/qualite",
            )

    @action(detail=True, methods=["post"], url_path="changer-statut")
    def changer_statut(self, request, pk=None):
        """Fait avancer l'action corrective dans son cycle de vie (verrou
        verification d'efficacite obligatoire avant cloture — cf.
        TRANSITIONS_ACTION). Cloture la non-conformite parente automatiquement
        des lors que toutes ses actions correctives sont elles-memes cloturees."""
        action_corrective = self.get_object()
        nouveau_statut = request.data.get("statut")

        if nouveau_statut not in dict(ActionCorrectiveDAE.STATUT_CHOICES):
            return Response({"error": "Statut invalide."}, status=status.HTTP_400_BAD_REQUEST)
        transitions_valides = TRANSITIONS_ACTION.get(action_corrective.statut, [])
        if nouveau_statut not in transitions_valides:
            return Response(
                {"error": f"Transition {action_corrective.statut} → {nouveau_statut} non autorisée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action_corrective.statut == "REALISEE" and nouveau_statut == "VERIFIEE":
            efficace = request.data.get("efficace")
            if efficace is None:
                return Response(
                    {"error": "La vérification d'efficacité nécessite une décision (efficace / non efficace)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            action_corrective.efficace = bool(efficace) if not isinstance(efficace, bool) else efficace
            action_corrective.verification_efficacite = request.data.get("verification_efficacite", "")
            action_corrective.date_verification = timezone.now().date()

        if nouveau_statut == "CLOTUREE" and not action_corrective.efficace:
            return Response(
                {"error": "Impossible de clôturer : l'efficacité de l'action n'a pas été confirmée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ancien_statut = action_corrective.statut
        action_corrective.statut = nouveau_statut
        if nouveau_statut == "REALISEE" and not action_corrective.date_realisation:
            action_corrective.date_realisation = timezone.now().date()
        action_corrective.save()

        log_historique_dae(
            action_corrective, request.user, "Statut modifié",
            ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut,
        )

        if nouveau_statut == "CLOTUREE":
            nc = action_corrective.non_conformite
            if not nc.actions_correctives.exclude(statut="CLOTUREE").exists():
                nc.statut = "CLOTUREE"
                nc.save(update_fields=["statut"])
                log_historique_dae(nc, request.user, "Statut modifié", nouvelle_valeur="Clôturée (actions correctives closes)")

        return Response(ActionCorrectiveDAESerializer(action_corrective).data)


class AuditQualiteDAEViewSet(viewsets.ModelViewSet):
    queryset = AuditQualiteDAE.objects.all()
    serializer_class = AuditQualiteDAESerializer
    permission_classes = [DAE_ENCADREMENT]


class QualiteKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_qualite_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
