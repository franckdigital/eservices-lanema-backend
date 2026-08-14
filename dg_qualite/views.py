from django.db.models import Avg, Count
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_dg_service_queryset

from .models import (
    ActionQualite,
    AuditQualite,
    IndicateurQualite,
    NonConformiteQualite,
    ReclamationClient,
    RevueDirection,
)
from .serializers import (
    ActionQualiteSerializer,
    AuditQualiteSerializer,
    IndicateurQualiteSerializer,
    NonConformiteQualiteSerializer,
    ReclamationClientSerializer,
    RevueDirectionSerializer,
)


def compute_qualite_kpis(date_debut=None, date_fin=None, request=None):
    """Calcule les 13 KPI Qualite (ISO/organisationnel). Reutilisable directement
    par le dashboard DG. Si `request` est fourni, restreint au meme perimetre
    (Service + proprietaire) que les listes CRUD de l'utilisateur courant."""
    non_conformites = NonConformiteQualite.objects.all()
    audits = AuditQualite.objects.all()
    actions = ActionQualite.objects.all()
    reclamations = ReclamationClient.objects.all()
    revues_qs = RevueDirection.objects.all()
    indicateurs_qs = IndicateurQualite.objects.all()
    if request is not None:
        non_conformites = scope_dg_service_queryset(non_conformites, request, 'Qualité')
        audits = scope_dg_service_queryset(audits, request, 'Qualité')
        actions = scope_dg_service_queryset(actions, request, 'Qualité', owner_field='responsable')
        reclamations = scope_dg_service_queryset(reclamations, request, 'Qualité')
        revues_qs = scope_dg_service_queryset(revues_qs, request, 'Qualité')
        indicateurs_qs = scope_dg_service_queryset(indicateurs_qs, request, 'Qualité')

    if date_debut and date_fin:
        non_conformites = non_conformites.filter(date_detection__range=(date_debut, date_fin))

    audits_avec_resultat = audits.exclude(resultat="")
    nb_audits_conformes = audits_avec_resultat.filter(resultat="CONFORME").count()
    nb_audits_avec_resultat = audits_avec_resultat.count()
    taux_conformite = round(nb_audits_conformes / nb_audits_avec_resultat * 100, 1) if nb_audits_avec_resultat else None

    audits_iso = audits.filter(type_audit="ISO")
    audits_iso_avec_resultat = audits_iso.exclude(resultat="")
    nb_iso_conformes = audits_iso_avec_resultat.filter(resultat="CONFORME").count()
    nb_iso_avec_resultat = audits_iso_avec_resultat.count()
    taux_conformite_iso = round(nb_iso_conformes / nb_iso_avec_resultat * 100, 1) if nb_iso_avec_resultat else None

    actions_correctives = actions.filter(type="CORRECTIVE")
    nb_correctives = actions_correctives.count()
    nb_correctives_cloturees = actions_correctives.filter(statut="CLOTUREE").count()
    taux_cloture_correctives = round(nb_correctives_cloturees / nb_correctives * 100, 1) if nb_correctives else None
    nb_preventives = actions.filter(type="PREVENTIVE").count()

    nb_actions_total = actions.count()
    nb_actions_cloturees = actions.filter(statut="CLOTUREE").count()
    taux_amelioration_continue = round(nb_actions_cloturees / nb_actions_total * 100, 1) if nb_actions_total else None

    nb_reclamations = reclamations.count()
    reclamations_traitees = reclamations.filter(date_traitement__isnull=False)
    delai_moyen = None
    if reclamations_traitees.exists():
        delais = [
            (r.date_traitement - r.date_reception).days
            for r in reclamations_traitees
        ]
        delai_moyen = round(sum(delais) / len(delais), 1)

    satisfaction_moyenne = reclamations.filter(note_satisfaction__isnull=False).aggregate(
        moyenne=Avg("note_satisfaction")
    )["moyenne"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    nb_indicateurs_atteints = sum(1 for i in indicateurs_qs if i.atteint)

    return {
        "nombre_non_conformites": non_conformites.count(),
        "nombre_audits_internes": audits.filter(type_audit="INTERNE").count(),
        "nombre_audits_externes": audits.filter(type_audit="EXTERNE").count(),
        "taux_conformite_procedures": taux_conformite,
        "nombre_actions_correctives": nb_correctives,
        "taux_cloture_actions_correctives": taux_cloture_correctives,
        "nombre_actions_preventives": nb_preventives,
        "taux_satisfaction_client": taux_satisfaction,
        "nombre_reclamations": nb_reclamations,
        "delai_moyen_traitement_reclamations_jours": delai_moyen,
        "nombre_revues_direction": revues_qs.count(),
        "taux_conformite_iso": taux_conformite_iso,
        "taux_amelioration_continue": taux_amelioration_continue,
        "nombre_indicateurs_atteints": nb_indicateurs_atteints,
    }


DG_QUALITE_MEMBRE = direction_permission('DG_QUALITE')


class NonConformiteQualiteViewSet(viewsets.ModelViewSet):
    queryset = NonConformiteQualite.objects.select_related("service_concerne").all()
    serializer_class = NonConformiteQualiteSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité')


class ActionQualiteViewSet(viewsets.ModelViewSet):
    queryset = ActionQualite.objects.select_related("non_conformite", "responsable").all()
    serializer_class = ActionQualiteSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité', owner_field='responsable')


class AuditQualiteViewSet(viewsets.ModelViewSet):
    queryset = AuditQualite.objects.all()
    serializer_class = AuditQualiteSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité')


class ReclamationClientViewSet(viewsets.ModelViewSet):
    queryset = ReclamationClient.objects.all()
    serializer_class = ReclamationClientSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité')


class RevueDirectionViewSet(viewsets.ModelViewSet):
    queryset = RevueDirection.objects.all()
    serializer_class = RevueDirectionSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité')


class IndicateurQualiteViewSet(viewsets.ModelViewSet):
    queryset = IndicateurQualite.objects.all()
    serializer_class = IndicateurQualiteSerializer
    permission_classes = [DG_QUALITE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Qualité')


class QualiteKPIView(APIView):
    permission_classes = [DG_QUALITE_MEMBRE]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_qualite_kpis(date_debut, date_fin, request=request))


class QualiteDashboardDirecteurView(APIView):
    """Vue condensee Directeur : pilotage strategique qualite (conformite, ISO, satisfaction)."""

    permission_classes = [DG_QUALITE_MEMBRE]

    def get(self, request):
        kpis = compute_qualite_kpis()

        return Response({
            "taux_conformite_procedures": kpis["taux_conformite_procedures"],
            "taux_conformite_iso": kpis["taux_conformite_iso"],
            "taux_cloture_actions_correctives": kpis["taux_cloture_actions_correctives"],
            "taux_amelioration_continue": kpis["taux_amelioration_continue"],
            "taux_satisfaction_client": kpis["taux_satisfaction_client"],
            "delai_moyen_traitement_reclamations_jours": kpis["delai_moyen_traitement_reclamations_jours"],
            "nombre_indicateurs_atteints": kpis["nombre_indicateurs_atteints"],
            "nombre_indicateurs_total": IndicateurQualite.objects.count(),
            "nombre_non_conformites_ouvertes": NonConformiteQualite.objects.exclude(statut="CLOTUREE").count(),
            "nombre_revues_direction": kpis["nombre_revues_direction"],
        })


class QualiteDashboardChefServiceView(APIView):
    """Vue condensee Chef de service : suivi operationnel (non-conformites/actions a traiter, charge par responsable)."""

    permission_classes = [DG_QUALITE_MEMBRE]

    def get(self, request):
        non_conformites_a_traiter = NonConformiteQualite.objects.exclude(statut="CLOTUREE")
        actions_en_cours = ActionQualite.objects.exclude(statut="CLOTUREE")

        charge_par_responsable = list(
            actions_en_cours.exclude(responsable__isnull=True)
            .values("responsable__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        non_conformites_recentes = list(
            non_conformites_a_traiter.select_related("service_concerne").order_by("-date_detection")[:10].values(
                "reference", "gravite", "statut", "service_concerne__nom", "date_detection"
            )
        )

        return Response({
            "nombre_non_conformites_a_traiter": non_conformites_a_traiter.count(),
            "nombre_actions_en_cours": actions_en_cours.count(),
            "charge_actions_par_responsable": charge_par_responsable,
            "nombre_reclamations_ouvertes": ReclamationClient.objects.filter(statut="OUVERTE").count(),
            "non_conformites_recentes": non_conformites_recentes,
        })
