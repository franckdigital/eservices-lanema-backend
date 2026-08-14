from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import (
    CertificationAgentDMCT,
    EquipementReference,
    EtalonnageReference,
    FormationDMCT,
    MaintenancePreventiveReference,
    PanneEquipementReference,
)

DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')
from .serializers import (
    CertificationAgentDMCTSerializer,
    EquipementReferenceSerializer,
    EtalonnageReferenceSerializer,
    FormationDMCTSerializer,
    MaintenancePreventiveReferenceSerializer,
    PanneEquipementReferenceSerializer,
)

User = get_user_model()

TYPES_PRESTATION = ["CONTROLE", "ETALONNAGE", "VERIFICATION", "CERTIFICATION"]


def compute_equipements_reference_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Equipements de metrologie (categorie 5) de la DMCT."""
    equipements = EquipementReference.objects.all()
    total = equipements.count()
    hors_service = equipements.filter(statut="HORS_SERVICE").count()
    taux_disponibilite = round((total - hors_service) / total * 100, 1) if total else None

    pannes = PanneEquipementReference.objects.all()
    if date_debut and date_fin:
        pannes = pannes.filter(date_panne__range=(date_debut, date_fin))
    pannes_reparees = pannes.filter(date_reparation__isnull=False)
    temps_arret = [(p.date_reparation - p.date_panne).days for p in pannes_reparees]
    temps_moyen_indisponibilite = round(sum(temps_arret) / len(temps_arret), 1) if temps_arret else None

    etalonnages = EtalonnageReference.objects.all()
    if date_debut and date_fin:
        etalonnages = etalonnages.filter(date_etalonnage__range=(date_debut, date_fin))

    today = timezone.now().date()
    a_echeance = equipements.filter(date_prochain_etalonnage__lte=today + timedelta(days=30))

    maintenances = MaintenancePreventiveReference.objects.all()
    if date_debut and date_fin:
        maintenances = maintenances.filter(date_prevue__range=(date_debut, date_fin))
    total_maintenances = maintenances.count()
    respect_planning = (
        round(maintenances.filter(statut="REALISEE").count() / total_maintenances * 100, 1)
        if total_maintenances else None
    )

    etalons = equipements.filter(est_etalon=True)
    total_etalons = etalons.count()
    taux_disponibilite_etalons = (
        round(etalons.exclude(statut="HORS_SERVICE").count() / total_etalons * 100, 1) if total_etalons else None
    )

    return {
        "nombre_equipements_reference_disponibles": equipements.exclude(statut="HORS_SERVICE").count(),
        "taux_disponibilite_equipements": taux_disponibilite,
        "nombre_pannes": pannes.count(),
        "temps_moyen_indisponibilite_jours": temps_moyen_indisponibilite,
        "nombre_etalonnages_realises": etalonnages.count(),
        "nombre_equipements_echeance_etalonnage": a_echeance.count(),
        "respect_planning_maintenance": respect_planning,
        "taux_disponibilite_etalons": taux_disponibilite_etalons,
    }


def compute_rh_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Ressources Humaines (categorie 7) de la DMCT, a
    partir des prestations (dmct_prestations) croisees avec les
    certifications (cette app)."""
    from dmct_prestations.models import PrestationDMCT

    prestations = PrestationDMCT.objects.filter(agent__isnull=False)
    if date_debut and date_fin:
        prestations = prestations.filter(date_debut__date__range=(date_debut, date_fin))

    agents_ids = list(prestations.values_list("agent", flat=True).distinct())
    nb_agents = len(agents_ids)

    par_agent = []
    total_realisees = 0
    durees = []
    for agent_id in agents_ids:
        prestations_agent = prestations.filter(agent_id=agent_id)
        terminees_agent = prestations_agent.filter(statut="TERMINEE", date_debut__isnull=False, date_fin__isnull=False)
        total_realisees += terminees_agent.count()
        for p in terminees_agent:
            durees.append((p.date_fin - p.date_debut).total_seconds() / 3600)
        types_traites = set(prestations_agent.values_list("type_prestation", flat=True).distinct())
        agent = User.objects.filter(id=agent_id).first()
        par_agent.append({
            "agent": (agent.get_full_name() or agent.username) if agent else str(agent_id),
            "prestations_realisees": terminees_agent.count(),
            "prestations_en_cours": prestations_agent.filter(statut="EN_COURS").count(),
            "taux_polyvalence": round(len(types_traites) / len(TYPES_PRESTATION) * 100, 1),
        })

    temps_moyen_intervention = round(sum(durees) / len(durees), 1) if durees else None

    en_cours_total = prestations.filter(statut="EN_COURS").count()
    taux_occupation = round(en_cours_total / nb_agents * 100, 1) if nb_agents else None

    if date_debut and date_fin:
        formations = FormationDMCT.objects.filter(date_formation__range=(date_debut, date_fin))
    else:
        formations = FormationDMCT.objects.all()
    heures_formation = formations.aggregate(t=Sum("duree_heures"))["t"]
    heures_formation = float(heures_formation) if heures_formation is not None else None

    today = timezone.now().date()
    certifications = CertificationAgentDMCT.objects.filter(agent_id__in=agents_ids)
    nb_certifs_valides = certifications.filter(
        date_expiration__isnull=True
    ).count() + certifications.filter(date_expiration__gte=today).count()
    taux_certification = round(nb_certifs_valides / nb_agents * 100, 1) if nb_agents else None

    return {
        "par_agent": par_agent,
        "nombre_prestations_realisees_total": total_realisees,
        "temps_moyen_intervention_heures": temps_moyen_intervention,
        "taux_occupation_agents": taux_occupation,
        "heures_formation_total": heures_formation,
        "taux_certification_agents": taux_certification,
        "taux_polyvalence_moyen": (
            round(sum(p["taux_polyvalence"] for p in par_agent) / len(par_agent), 1) if par_agent else None
        ),
    }


class EquipementReferenceViewSet(viewsets.ModelViewSet):
    queryset = EquipementReference.objects.all()
    serializer_class = EquipementReferenceSerializer
    permission_classes = [DMCT_ENCADREMENT]


class PanneEquipementReferenceViewSet(viewsets.ModelViewSet):
    queryset = PanneEquipementReference.objects.select_related("equipement").all()
    serializer_class = PanneEquipementReferenceSerializer
    permission_classes = [DMCT_ENCADREMENT]


class MaintenancePreventiveReferenceViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePreventiveReference.objects.select_related("equipement").all()
    serializer_class = MaintenancePreventiveReferenceSerializer
    permission_classes = [DMCT_ENCADREMENT]


class EtalonnageReferenceViewSet(viewsets.ModelViewSet):
    queryset = EtalonnageReference.objects.select_related("equipement").all()
    serializer_class = EtalonnageReferenceSerializer
    permission_classes = [DMCT_ENCADREMENT]


class CertificationAgentDMCTViewSet(viewsets.ModelViewSet):
    queryset = CertificationAgentDMCT.objects.select_related("agent").all()
    serializer_class = CertificationAgentDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class FormationDMCTViewSet(viewsets.ModelViewSet):
    queryset = FormationDMCT.objects.all()
    serializer_class = FormationDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class EquipementsReferenceKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_equipements_reference_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class RHKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_rh_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
