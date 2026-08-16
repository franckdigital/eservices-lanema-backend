from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils import timezone

from rest_framework import permissions
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import HistoriqueActionDAE, PieceJointeDAE
from .serializers import HistoriqueActionDAESerializer, PieceJointeDAESerializer

DAE_MEMBRE = direction_permission('DAE')

from aero_atelier.views import compute_equipements_atelier_kpis, compute_personnel_kpis
from aero_clients.views import compute_clients_kpis
from aero_finance.views import compute_financiers_kpis
from aero_maintenance.models import OrdreTravail
from aero_maintenance.views import compute_batteries_kpis, compute_maintenance_kpis, compute_roues_kpis
from aero_qualite.views import compute_qualite_kpis
from aero_securite.views import compute_securite_kpis
from aero_stock.models import PieceRechange
from aero_stock.views import compute_stock_kpis


def compute_strategique_kpis(maintenance, securite, qualite, date_debut=None, date_fin=None):
    """Calcule les 9 KPI strategiques (categorie 11) de la DAE, a partir des
    dicts deja calcules par les autres fonctions compute_*_kpis (pas de
    recalcul)."""
    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    aeronefs_apres_intervention = ordres.filter(
        statut__in=["TERMINE", "VALIDE", "CLOTURE"], aeronef__statut="EN_SERVICE"
    ).values("aeronef").distinct().count()
    total_aeronefs_intervenus = ordres.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"]).values("aeronef").distinct().count()
    disponibilite_apres_intervention = (
        round(aeronefs_apres_intervention / total_aeronefs_intervenus * 100, 1)
        if total_aeronefs_intervenus else None
    )

    taux_reprise = 100 - qualite.get("taux_reussite_premier_passage") if qualite.get("taux_reussite_premier_passage") is not None else None
    taux_fiabilite_reparations = round(100 - taux_reprise, 1) if taux_reprise is not None else None

    composantes = [
        (maintenance.get("taux_respect_delais"), 0.25),
        (securite.get("taux_conformite_anac"), 0.25),
        (qualite.get("taux_reussite_premier_passage"), 0.25),
        (disponibilite_apres_intervention, 0.25),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    indice_global = (
        round(sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids, 1)
        if total_poids else None
    )

    from django.db.models.functions import TruncMonth

    six_mois = timezone.now().date() - timedelta(days=180)
    evolution_charge = list(
        OrdreTravail.objects.filter(date_demande__date__gte=six_mois)
        .annotate(mois=TruncMonth("date_demande"))
        .values("mois")
        .annotate(nombre_ordres=Count("id"))
        .order_by("mois")
    )
    evolution_productivite = list(
        OrdreTravail.objects.filter(date_demande__date__gte=six_mois, statut__in=["TERMINE", "VALIDE", "CLOTURE"])
        .annotate(mois=TruncMonth("date_demande"))
        .values("mois")
        .annotate(nombre_termines=Count("id"))
        .order_by("mois")
    )

    return {
        "disponibilite_aeronefs_apres_intervention": disponibilite_apres_intervention,
        "total_interventions": ordres.count(),
        "taux_conformite_reglementaire": securite.get("taux_conformite_anac"),
        "respect_contrats_sla": maintenance.get("taux_respect_delais"),
        "taux_fiabilite_reparations": taux_fiabilite_reparations,
        "pct_reparations_sans_reprise": qualite.get("taux_reussite_premier_passage"),
        "indice_global_performance_dae": indice_global,
        "evolution_mensuelle_charge_travail": evolution_charge,
        "evolution_mensuelle_productivite": evolution_productivite,
    }


class DashboardDAEView(APIView):
    """Tableau de bord decisionnel DAE : agrege les 11 categories de KPI de la
    Direction de l'Aeronautique (clients, stock, maintenance, roues,
    batteries, qualite, securite, equipements d'atelier, personnel,
    financiers) + performance strategique."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        clients = compute_clients_kpis(date_debut, date_fin)
        stock = compute_stock_kpis(date_debut, date_fin)
        maintenance = compute_maintenance_kpis(date_debut, date_fin)
        roues = compute_roues_kpis(date_debut, date_fin)
        batteries = compute_batteries_kpis(date_debut, date_fin)
        qualite = compute_qualite_kpis(date_debut, date_fin)
        securite = compute_securite_kpis(date_debut, date_fin)
        equipements_atelier = compute_equipements_atelier_kpis(date_debut, date_fin)
        personnel = compute_personnel_kpis(date_debut, date_fin)
        financiers = compute_financiers_kpis(date_debut, date_fin)
        strategique = compute_strategique_kpis(maintenance, securite, qualite, date_debut, date_fin)

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "clients": clients,
            "stock": stock,
            "maintenance": maintenance,
            "roues": roues,
            "batteries": batteries,
            "qualite": qualite,
            "securite": securite,
            "equipements_atelier": equipements_atelier,
            "personnel": personnel,
            "financiers": financiers,
            "strategique": strategique,
        })


class DashboardDAEDirecteurView(APIView):
    """Vue condensee Directeur de l'Aeronautique (9 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        maintenance = compute_maintenance_kpis()
        securite = compute_securite_kpis()
        qualite = compute_qualite_kpis()
        personnel = compute_personnel_kpis()
        financiers = compute_financiers_kpis()
        strategique = compute_strategique_kpis(maintenance, securite, qualite)

        interventions_en_cours = OrdreTravail.objects.filter(statut="EN_COURS").count()
        today = timezone.now().date()
        travaux_en_retard = OrdreTravail.objects.filter(
            date_fin_prevue__lt=today
        ).exclude(statut__in=["TERMINE", "VALIDE", "CLOTURE", "ANNULE"]).count()

        pieces_critiques_en_alerte = PieceRechange.objects.filter(
            est_critique=True, quantite_stock__lte=0
        ).count()

        return Response({
            "interventions_en_cours": interventions_en_cours,
            "travaux_en_retard": travaux_en_retard,
            "taux_occupation_techniciens": personnel["taux_occupation_techniciens"],
            "taux_disponibilite_equipements": None,
            "respect_delais": maintenance["taux_respect_delais"],
            "conformite_anac": securite["taux_conformite_anac"],
            "productivite_par_equipe": personnel["par_technicien"],
            "chiffre_affaires": financiers["ca_prestations"],
            "equipements_critiques_en_alerte": pieces_critiques_en_alerte,
            "indice_global_performance": strategique["indice_global_performance_dae"],
        })


class DashboardDAEChefAtelierView(APIView):
    """Vue condensee Chef d'atelier (6 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        ordres_du_jour = OrdreTravail.objects.filter(date_demande__date=today)
        reparations_terminees = OrdreTravail.objects.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"], date_fin=today)
        interventions_urgentes = OrdreTravail.objects.filter(
            type_intervention="URGENCE"
        ).exclude(statut__in=["TERMINE", "VALIDE", "CLOTURE", "ANNULE"])
        pieces_en_rupture = PieceRechange.objects.filter(quantite_stock__lte=0)

        charge_par_technicien = list(
            OrdreTravail.objects.filter(statut="EN_COURS")
            .exclude(technicien__isnull=True)
            .values("technicien__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        from aero_atelier.models import EquipementAtelier

        equipements_indisponibles = EquipementAtelier.objects.filter(
            statut__in=["HORS_SERVICE", "MAINTENANCE"]
        ).count()

        return Response({
            "ordres_travail_du_jour": ordres_du_jour.count(),
            "reparations_terminees": reparations_terminees.count(),
            "interventions_urgentes": interventions_urgentes.count(),
            "pieces_en_rupture": pieces_en_rupture.count(),
            "charge_travail_techniciens": charge_par_technicien,
            "equipements_indisponibles": equipements_indisponibles,
        })


class DashboardDAETechnicienView(APIView):
    """Vue condensee Technicien, scopee sur request.user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        ordres_user = OrdreTravail.objects.filter(technicien=request.user)
        ordres_termines = ordres_user.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"], date_debut__isnull=False, date_fin__isnull=False)

        durees = [(o.date_fin - o.date_debut.date()).days for o in ordres_termines]
        temps_moyen = round(sum(durees) / len(durees), 1) if durees else None

        objectifs_jour = ordres_user.filter(date_demande__date=today).count()

        total_user = ordres_user.count()
        termines_count = ordres_termines.count()
        score_performance = round(termines_count / total_user * 100, 1) if total_user else None

        from aero_qualite.models import NonConformiteDAE

        historique_reparations = list(
            ordres_termines.order_by("-date_fin")[:10].values(
                "reference", "type_intervention", "date_debut", "date_fin", "statut"
            )
        )

        return Response({
            "interventions_assignees": total_user,
            "interventions_en_cours": ordres_user.filter(statut="EN_COURS").count(),
            "temps_moyen_par_intervention_jours": temps_moyen,
            "maintenance_planifiee": ordres_user.filter(statut__in=["A_PLANIFIER", "PLANIFIE"]).count(),
            "historique_reparations": historique_reparations,
            "objectifs_quotidiens": objectifs_jour,
            "non_conformites_liees": NonConformiteDAE.objects.filter(
                ordre_travail__technicien=request.user
            ).count(),
            "score_performance": score_performance,
        })


def _resolve_dae_content_type(request):
    """Resout le ContentType cible depuis app_label/model (query params),
    pour les endpoints transverses Historique/Pieces jointes — evite d'exposer
    un id de ContentType brut cote frontend."""
    app_label = request.query_params.get("app_label")
    model = request.query_params.get("model")
    if not app_label or not model:
        return None
    try:
        return ContentType.objects.get(app_label=app_label, model=model.lower())
    except ContentType.DoesNotExist:
        return None


class HistoriqueActionDAEListView(APIView):
    """GET /api/dae/dashboard/historique/?app_label=aero_maintenance&model=ordretravail&object_id=5"""

    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        content_type = _resolve_dae_content_type(request)
        object_id = request.query_params.get("object_id")
        if content_type is None or not object_id:
            return Response({"error": "app_label, model et object_id sont requis."}, status=400)
        qs = HistoriqueActionDAE.objects.filter(content_type=content_type, object_id=object_id).select_related("utilisateur")
        return Response(HistoriqueActionDAESerializer(qs, many=True).data)


class PieceJointeDAEListCreateView(APIView):
    """GET/POST /api/dae/dashboard/pieces-jointes/?app_label=...&model=...&object_id=..."""

    permission_classes = [DAE_MEMBRE]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        content_type = _resolve_dae_content_type(request)
        object_id = request.query_params.get("object_id")
        if content_type is None or not object_id:
            return Response({"error": "app_label, model et object_id sont requis."}, status=400)
        qs = PieceJointeDAE.objects.filter(content_type=content_type, object_id=object_id).select_related("uploaded_by")
        return Response(PieceJointeDAESerializer(qs, many=True, context={"request": request}).data)

    def post(self, request):
        content_type = _resolve_dae_content_type(request)
        object_id = request.query_params.get("object_id")
        fichier = request.FILES.get("fichier")
        if content_type is None or not object_id:
            return Response({"error": "app_label, model et object_id sont requis."}, status=400)
        if not fichier:
            return Response({"error": "Fichier requis."}, status=400)
        piece = PieceJointeDAE.objects.create(
            content_type=content_type, object_id=object_id, fichier=fichier, uploaded_by=request.user,
        )
        return Response(PieceJointeDAESerializer(piece, context={"request": request}).data, status=201)
