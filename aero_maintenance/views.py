from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_queryset_to_owner

from .models import BatterieAeronef, InspectionRoue, OrdreTravail, RoueAeronef

# Page "Maintenance" : seule page opérationnelle accessible au palier "terrain"
# (technicien) — mais un technicien ne voit/modifie que ses propres ordres de
# travail (scope_queryset_to_owner ci-dessous). Roues/Inspections/Batteries
# n'ont pas de "propriétaire" individuel : visibles à tout membre DAE.
DAE_MEMBRE = direction_permission('DAE')
from .serializers import (
    BatterieAeronefSerializer,
    InspectionRoueSerializer,
    OrdreTravailSerializer,
    RoueAeronefSerializer,
)


def compute_maintenance_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI de maintenance (categorie 1) de la DAE. Reutilisable
    directement par le tableau de bord DAE."""
    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    termines = ordres.filter(statut="TERMINE")

    prises_en_charge = ordres.filter(date_prise_charge__isnull=False)
    delais_prise_charge = [
        (o.date_prise_charge - o.date_demande).total_seconds() / 3600 for o in prises_en_charge
    ]
    temps_moyen_prise_en_charge = round(sum(delais_prise_charge) / len(delais_prise_charge), 1) if delais_prise_charge else None

    termines_avec_debut = termines.filter(date_debut__isnull=False, date_fin__isnull=False)
    mttr_list = [(o.date_fin - o.date_debut.date()).days for o in termines_avec_debut]
    mttr_jours = round(sum(mttr_list) / len(mttr_list), 1) if mttr_list else None

    termines_avec_prevue = termines.filter(date_fin_prevue__isnull=False, date_fin__isnull=False)
    ecarts_livraison = [(o.date_fin - o.date_fin_prevue).days for o in termines_avec_prevue]
    delai_moyen_livraison = round(sum(ecarts_livraison) / len(ecarts_livraison), 1) if ecarts_livraison else None

    nb_termines_avec_prevue = termines_avec_prevue.count()
    nb_dans_les_delais = sum(1 for o in termines_avec_prevue if o.date_fin <= o.date_fin_prevue)
    pct_travaux_dans_delais = (
        round(nb_dans_les_delais / nb_termines_avec_prevue * 100, 1) if nb_termines_avec_prevue else None
    )

    today = timezone.now().date()
    ordres_avec_prevue = ordres.filter(date_fin_prevue__isnull=False)
    nb_respectes = sum(
        1 for o in ordres_avec_prevue
        if (o.date_fin and o.date_fin <= o.date_fin_prevue) or (not o.date_fin and today <= o.date_fin_prevue)
    )
    taux_respect_delais = (
        round(nb_respectes / ordres_avec_prevue.count() * 100, 1) if ordres_avec_prevue.exists() else None
    )

    par_technicien = []
    techniciens_ids = ordres.filter(technicien__isnull=False).values_list("technicien", flat=True).distinct()
    for tech_id in techniciens_ids:
        ordres_tech = ordres.filter(technicien_id=tech_id)
        technicien = ordres_tech.first().technicien
        par_technicien.append({
            "technicien": technicien.get_full_name() or technicien.username,
            "nombre_interventions": ordres_tech.count(),
        })

    return {
        "demandes_totales": ordres.count(),
        "preventives_realisees": termines.filter(type_intervention="PREVENTIVE").count(),
        "correctives_realisees": termines.filter(type_intervention="CORRECTIVE").count(),
        "urgences_realisees": termines.filter(type_intervention="URGENCE").count(),
        "temps_moyen_prise_en_charge_heures": temps_moyen_prise_en_charge,
        "mttr_jours": mttr_jours,
        "delai_moyen_livraison_jours": delai_moyen_livraison,
        "taux_respect_delais": taux_respect_delais,
        "pct_travaux_termines_dans_delais": pct_travaux_dans_delais,
        "interventions_par_technicien": par_technicien,
    }


def compute_roues_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Roues d'aeronefs (categorie 2) de la DAE."""
    inspections = InspectionRoue.objects.all()
    if date_debut and date_fin:
        inspections = inspections.filter(date_inspection__range=(date_debut, date_fin))

    roues = RoueAeronef.objects.all()

    taux_conformite = (
        round(inspections.filter(conforme=True).count() / inspections.count() * 100, 1)
        if inspections.exists() else None
    )

    reparations = inspections.filter(type_inspection="REPARATION", ordre_travail__isnull=False)
    delais_reparation = []
    for insp in reparations.select_related("ordre_travail"):
        ot = insp.ordre_travail
        if ot.date_debut and ot.date_fin:
            delais_reparation.append((ot.date_fin - ot.date_debut.date()).days)
    temps_moyen_reparation = round(sum(delais_reparation) / len(delais_reparation), 1) if delais_reparation else None

    cycles = [r.nombre_cycles for r in roues]
    cycles_moyens = round(sum(cycles) / len(cycles), 1) if cycles else None

    return {
        "nombre_roues_inspectees": inspections.count(),
        "nombre_roues_reparees": roues.filter(statut="REPAREE").count(),
        "nombre_roues_remplacees": roues.filter(statut="REMPLACEE").count(),
        "nombre_roues_non_conformes": roues.filter(statut="NON_CONFORME").count(),
        "taux_conformite_roues": taux_conformite,
        "temps_moyen_reparation_jours": temps_moyen_reparation,
        "cycles_moyens": cycles_moyens,
        "nombre_inspections_periodiques": inspections.filter(type_inspection="INSPECTION_PERIODIQUE").count(),
    }


def compute_batteries_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Batteries d'aeronefs (categorie 3) de la DAE."""
    batteries = BatterieAeronef.objects.all()
    total = batteries.count()
    hors_service = batteries.filter(statut="HORS_SERVICE")

    taux_conformite = round((total - hors_service.count()) / total * 100, 1) if total else None

    fin_de_vie = hors_service.filter(date_mise_en_service__isnull=False, date_derniere_maintenance__isnull=False)
    durees_vie = [(b.date_derniere_maintenance - b.date_mise_en_service).days for b in fin_de_vie]
    duree_vie_moyenne = round(sum(durees_vie) / len(durees_vie), 1) if durees_vie else None

    return {
        "nombre_batteries_testees": batteries.filter(statut="EN_TEST").count(),
        "nombre_batteries_rechargees": batteries.filter(statut="RECHARGEE").count(),
        "nombre_batteries_reparees": batteries.filter(statut="REPAREE").count(),
        "nombre_batteries_remplacees": batteries.filter(statut="REMPLACEE").count(),
        "nombre_batteries_hors_service": hors_service.count(),
        "taux_conformite_batteries": taux_conformite,
        "temps_moyen_maintenance_jours": None,
        "temps_moyen_maintenance_jours_note": "Non mesurable : aucune duree d'intervention dediee n'est enregistree pour les batteries.",
        "duree_vie_moyenne_jours": duree_vie_moyenne,
    }


class OrdreTravailViewSet(viewsets.ModelViewSet):
    queryset = OrdreTravail.objects.select_related("aeronef", "technicien", "piece_utilisee").all()
    serializer_class = OrdreTravailSerializer
    permission_classes = [DAE_MEMBRE]

    def get_queryset(self):
        return scope_queryset_to_owner(super().get_queryset(), self.request, "technicien")

    def perform_create(self, serializer):
        from core.direction_access import user_tier
        if user_tier(self.request.user) == 'terrain' and not serializer.validated_data.get('technicien'):
            serializer.save(technicien=self.request.user)
        else:
            serializer.save()


class RoueAeronefViewSet(viewsets.ModelViewSet):
    queryset = RoueAeronef.objects.select_related("aeronef").all()
    serializer_class = RoueAeronefSerializer
    permission_classes = [DAE_MEMBRE]


class InspectionRoueViewSet(viewsets.ModelViewSet):
    queryset = InspectionRoue.objects.select_related("roue", "ordre_travail").all()
    serializer_class = InspectionRoueSerializer
    permission_classes = [DAE_MEMBRE]


class BatterieAeronefViewSet(viewsets.ModelViewSet):
    queryset = BatterieAeronef.objects.select_related("aeronef").all()
    serializer_class = BatterieAeronefSerializer
    permission_classes = [DAE_MEMBRE]


class MaintenanceKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_maintenance_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class RouesKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_roues_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class BatteriesKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_batteries_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
