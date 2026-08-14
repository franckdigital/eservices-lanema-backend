from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Courrier, Diligence, Direction, Presence, Service
from dg_communication.views import compute_communication_kpis
from dg_juridique.models import Contentieux, Contrat
from dg_juridique.views import compute_juridique_kpis
from dg_patrimoine.views import compute_patrimoine_kpis
from dg_qualite.models import NonConformiteQualite
from dg_qualite.views import compute_qualite_kpis
from projet.models import Projet

from core.views_kpi_ged import compute_ged_kpis

from .models import ObjectifStrategique
from .serializers import ObjectifStrategiqueSerializer


def _diligences_par_direction():
    """Indice de performance simple par Direction, base sur les diligences
    (taux de completion + taux de retard). Calcul autonome, independant de
    ExecutiveKPIView (aucun import de ses fonctions privees, pour ne pas
    creer de couplage fragile avec ce fichier deja tres volumineux)."""
    resultats = []
    today = timezone.now().date()
    for direction in Direction.objects.all():
        diligences = Diligence.objects.filter(direction=direction)
        total = diligences.count()
        if not total:
            continue
        terminees = diligences.filter(statut__in=["termine", "archivee"]).count()
        en_retard = diligences.filter(
            date_limite__lt=today, statut__in=["en_attente", "en_cours", "en_correction", "demande_validation"]
        ).count()
        taux_completion = round(terminees / total * 100, 1)
        taux_retard = round(en_retard / total * 100, 1)
        indice = round(taux_completion - taux_retard * 0.5, 1)
        resultats.append({
            "direction": direction.nom,
            "total_diligences": total,
            "taux_completion": taux_completion,
            "taux_retard": taux_retard,
            "indice_performance": max(0, indice),
        })
    resultats.sort(key=lambda r: r["indice_performance"], reverse=True)
    return resultats


def _courriers_par_service():
    """Indice de performance simple par Service, base sur le traitement des courriers."""
    resultats = []
    for service in Service.objects.all():
        courriers = Courrier.objects.filter(service=service)
        total = courriers.count()
        if not total:
            continue
        traites = courriers.filter(statut__in=["traite", "termine", "archive"]).count()
        taux_traitement = round(traites / total * 100, 1)
        resultats.append({
            "service": service.nom,
            "total_courriers": total,
            "taux_traitement": taux_traitement,
            "indice_performance": taux_traitement,
        })
    resultats.sort(key=lambda r: r["indice_performance"], reverse=True)
    return resultats


def _pilotage_strategique():
    today = timezone.now().date()

    projets = Projet.objects.all()
    projets_avec_budget = projets.exclude(budget_prevu__isnull=True).exclude(budget_prevu=0)
    budget_prevu_total = projets_avec_budget.aggregate(total=Sum("budget_prevu"))["total"] or 0
    budget_consomme_total = projets_avec_budget.aggregate(total=Sum("budget_consomme"))["total"] or 0
    taux_execution_budget = (
        round(float(budget_consomme_total) / float(budget_prevu_total) * 100, 1) if budget_prevu_total else None
    )

    projets_strategiques = projets.filter(est_strategique=True)
    nb_projets_strategiques_en_cours = projets_strategiques.filter(statut__in=["planifie", "en_cours"]).count()
    nb_projets_strategiques_acheves = projets_strategiques.filter(statut="termine").count()

    objectifs = ObjectifStrategique.objects.filter(type="OBJECTIF")
    taux_realisation_objectifs = None
    if objectifs.exists():
        taux = [o.taux_realisation for o in objectifs if o.taux_realisation is not None]
        taux_realisation_objectifs = round(sum(taux) / len(taux), 1) if taux else None

    digitalisation = ObjectifStrategique.objects.filter(type="DIGITALISATION")
    taux_digitalisation = None
    if digitalisation.exists():
        taux = [o.taux_realisation for o in digitalisation if o.taux_realisation is not None]
        taux_digitalisation = round(sum(taux) / len(taux), 1) if taux else None

    diligences = Diligence.objects.all()
    total_diligences = diligences.count()
    diligences_terminees = diligences.filter(statut__in=["termine", "archivee"]).count()
    diligences_en_retard = diligences.filter(
        date_limite__lt=today, statut__in=["en_attente", "en_cours", "en_correction", "demande_validation"]
    ).count()
    taux_respect_delais = (
        round((total_diligences - diligences_en_retard) / total_diligences * 100, 1) if total_diligences else None
    )

    courriers_traites = Courrier.objects.filter(statut__in=["traite", "termine", "archive"]).count()
    total_prestations_realisees = diligences_terminees + courriers_traites

    nb_agents_actifs = User.objects.filter(is_active=True).count()
    productivite_globale = (
        round(diligences_terminees / nb_agents_actifs, 2) if nb_agents_actifs else None
    )

    return {
        "taux_global_realisation_objectifs": taux_realisation_objectifs,
        "taux_execution_budget": taux_execution_budget,
        "taux_digitalisation_processus": taux_digitalisation,
        "nombre_total_prestations_realisees": total_prestations_realisees,
        "taux_respect_delais_sla": taux_respect_delais,
        "nombre_projets_strategiques_en_cours": nb_projets_strategiques_en_cours,
        "nombre_projets_strategiques_acheves": nb_projets_strategiques_acheves,
        "productivite_globale_agents": productivite_globale,
        "indice_performance_directions": _diligences_par_direction(),
        "indice_performance_services": _courriers_par_service(),
    }


def _alertes():
    today = timezone.now().date()
    diligences_critiques_non_traitees = Diligence.objects.filter(
        categorie="URGENT"
    ).exclude(statut__in=["termine", "archivee"]).count()
    diligences_en_retard = Diligence.objects.filter(
        date_limite__lt=today
    ).exclude(statut__in=["termine", "archivee"]).count()
    contentieux_en_cours = Contentieux.objects.filter(statut="EN_COURS").count()
    non_conformites_ouvertes = NonConformiteQualite.objects.exclude(statut="CLOTUREE").count()
    contrats_bientot_expires = Contrat.objects.filter(
        date_expiration__isnull=False,
        date_expiration__range=(today, today + timezone.timedelta(days=30)),
    ).count()

    return {
        "dossiers_critiques_non_traites": diligences_critiques_non_traitees,
        "dossiers_en_retard": diligences_en_retard,
        "contentieux_en_cours": contentieux_en_cours,
        "non_conformites_ouvertes": non_conformites_ouvertes,
        "contrats_bientot_expires_30j": contrats_bientot_expires,
    }


class DashboardDGView(APIView):
    """Tableau de bord executif de la Directrice Generale : agrege les 5 domaines
    KPI decisionnels (Communication, GED, Patrimoine, Qualite, Juridique) plus
    le pilotage strategique global et les alertes.

    N'ecrase pas /api/executive-kpi/ (ExecutiveKPIView, deja consomme par
    ExecutiveDashboard.js) : nouvel endpoint dedie, calculs autonomes."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "pilotage_strategique": _pilotage_strategique(),
            "alertes": _alertes(),
            "communication": compute_communication_kpis(date_debut, date_fin),
            "ged": compute_ged_kpis(date_debut, date_fin),
            "patrimoine": compute_patrimoine_kpis(date_debut, date_fin),
            "qualite": compute_qualite_kpis(date_debut, date_fin),
            "juridique": compute_juridique_kpis(date_debut, date_fin),
        })


class ObjectifStrategiqueViewSet(viewsets.ModelViewSet):
    queryset = ObjectifStrategique.objects.select_related("direction", "service").all()
    serializer_class = ObjectifStrategiqueSerializer
    permission_classes = [permissions.IsAuthenticated]
