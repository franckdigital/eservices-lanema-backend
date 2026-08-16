from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_maintenance.models import OrdreTravail
from core.direction_access import direction_permission

from .models import (
    CertificationTechnicien,
    EquipementAtelier,
    EtalonnageAtelier,
    MaintenancePreventiveAtelier,
    PanneEquipementAtelier,
)

# Atelier : hors du périmètre "terrain" (leur page est Maintenance uniquement).
DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')
from .serializers import (
    CertificationTechnicienSerializer,
    EquipementAtelierSerializer,
    EtalonnageAtelierSerializer,
    MaintenancePreventiveAtelierSerializer,
    PanneEquipementAtelierSerializer,
)

User = get_user_model()

TYPES_INTERVENTION = ["PREVENTIVE", "CORRECTIVE", "URGENCE"]


def compute_equipements_atelier_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Equipements d'atelier (categorie 6) de la DAE."""
    equipements = EquipementAtelier.objects.all()
    total = equipements.count()
    hors_service = equipements.filter(statut="HORS_SERVICE").count()
    taux_disponibilite = round((total - hors_service) / total * 100, 1) if total else None

    pannes = PanneEquipementAtelier.objects.all()
    if date_debut and date_fin:
        pannes = pannes.filter(date_panne__range=(date_debut, date_fin))
    pannes_reparees = pannes.filter(date_reparation__isnull=False)
    temps_arret = [(p.date_reparation - p.date_panne).days for p in pannes_reparees]
    temps_moyen_arret = round(sum(temps_arret) / len(temps_arret), 1) if temps_arret else None

    maintenances = MaintenancePreventiveAtelier.objects.all()
    if date_debut and date_fin:
        maintenances = maintenances.filter(date_prevue__range=(date_debut, date_fin))
    total_maintenances = maintenances.count()
    taux_respect_planning = (
        round(maintenances.filter(statut="REALISEE").count() / total_maintenances * 100, 1)
        if total_maintenances else None
    )

    etalonnages = EtalonnageAtelier.objects.all()
    if date_debut and date_fin:
        etalonnages = etalonnages.filter(date_etalonnage__range=(date_debut, date_fin))

    return {
        "taux_disponibilite_equipements": taux_disponibilite,
        # KPI 13 du cahier des charges (categorie performance) : faute de
        # suivi d'heures d'usage par equipement, approxime par le taux de
        # disponibilite (equipement disponible = mobilisable pour les
        # interventions de la DAE).
        "taux_utilisation_equipements": taux_disponibilite,
        "nombre_pannes": pannes.count(),
        "temps_moyen_arret_jours": temps_moyen_arret,
        "taux_respect_planning_maintenance": taux_respect_planning,
        "nombre_etalonnages_realises": etalonnages.count(),
        "nombre_equipements_hors_service": hors_service,
    }


def compute_personnel_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Personnel (categorie 7) de la DAE, a partir des
    ordres de travail (aero_maintenance) croises avec les certifications
    (cette app)."""
    ordres = OrdreTravail.objects.filter(technicien__isnull=False)
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    techniciens_ids = list(ordres.values_list("technicien", flat=True).distinct())
    nb_techniciens = len(techniciens_ids)

    productivite = []
    total_interventions_realisees = 0
    durees_interventions = []
    for tech_id in techniciens_ids:
        ordres_tech = ordres.filter(technicien_id=tech_id)
        termines_tech = ordres_tech.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"], date_debut__isnull=False, date_fin__isnull=False)
        total_interventions_realisees += termines_tech.count()
        for o in termines_tech:
            durees_interventions.append((o.date_fin - o.date_debut.date()).days)
        types_traites = set(ordres_tech.values_list("type_intervention", flat=True).distinct())
        technicien = User.objects.filter(id=tech_id).first()
        productivite.append({
            "technicien": (technicien.get_full_name() or technicien.username) if technicien else str(tech_id),
            "interventions_realisees": termines_tech.count(),
            "interventions_en_cours": ordres_tech.filter(statut="EN_COURS").count(),
            "taux_polyvalence": round(len(types_traites) / len(TYPES_INTERVENTION) * 100, 1),
        })

    temps_moyen_intervention = (
        round(sum(durees_interventions) / len(durees_interventions), 1) if durees_interventions else None
    )

    en_cours_total = ordres.filter(statut="EN_COURS").count()
    taux_occupation = round(en_cours_total / nb_techniciens * 100, 1) if nb_techniciens else None

    from aero_securite.models import FormationSecurite

    heures_formation_total = None
    if date_debut and date_fin:
        formations = FormationSecurite.objects.filter(date_formation__range=(date_debut, date_fin))
    else:
        formations = FormationSecurite.objects.all()
    heures_agg = formations.aggregate(t=Sum("duree_heures"))["t"]
    if heures_agg is not None:
        heures_formation_total = float(heures_agg)

    today = timezone.now().date()
    certifications = CertificationTechnicien.objects.filter(technicien_id__in=techniciens_ids)
    nb_certifs_valides = certifications.filter(
        date_expiration__isnull=True
    ).count() + certifications.filter(date_expiration__gte=today).count()
    taux_certification = (
        round(nb_certifs_valides / nb_techniciens * 100, 1) if nb_techniciens else None
    )

    return {
        "par_technicien": productivite,
        "nombre_interventions_realisees_total": total_interventions_realisees,
        "temps_moyen_intervention_jours": temps_moyen_intervention,
        "taux_occupation_techniciens": taux_occupation,
        "heures_formation_total": heures_formation_total,
        "taux_certification": taux_certification,
        "taux_polyvalence_moyen": (
            round(sum(p["taux_polyvalence"] for p in productivite) / len(productivite), 1) if productivite else None
        ),
    }


class EquipementAtelierViewSet(viewsets.ModelViewSet):
    queryset = EquipementAtelier.objects.all()
    serializer_class = EquipementAtelierSerializer
    permission_classes = [DAE_ENCADREMENT]


class PanneEquipementAtelierViewSet(viewsets.ModelViewSet):
    queryset = PanneEquipementAtelier.objects.select_related("equipement").all()
    serializer_class = PanneEquipementAtelierSerializer
    permission_classes = [DAE_ENCADREMENT]


class MaintenancePreventiveAtelierViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePreventiveAtelier.objects.select_related("equipement").all()
    serializer_class = MaintenancePreventiveAtelierSerializer
    permission_classes = [DAE_ENCADREMENT]


class EtalonnageAtelierViewSet(viewsets.ModelViewSet):
    queryset = EtalonnageAtelier.objects.select_related("equipement").all()
    serializer_class = EtalonnageAtelierSerializer
    permission_classes = [DAE_ENCADREMENT]


class CertificationTechnicienViewSet(viewsets.ModelViewSet):
    queryset = CertificationTechnicien.objects.select_related("technicien").all()
    serializer_class = CertificationTechnicienSerializer
    permission_classes = [DAE_ENCADREMENT]


class EquipementsAtelierKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_equipements_atelier_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class PersonnelKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_personnel_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
