import datetime

from django.db.models import Count, Sum
from django.utils import timezone

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from demandes.models import DemandeDevis
from facturation.models import Facture
from qualite.models import Essai

from .models import Rapport, RapportEssai
from .serializers import RapportEssaiSerializer, RapportSerializer


def _periode_bounds(periode):
    """Retourne (date_debut, date_fin) inclusives pour la période demandée."""
    now = timezone.localdate()

    if periode == "annee":
        debut = now.replace(month=1, day=1)
    elif periode == "trimestre":
        trimestre_index = (now.month - 1) // 3
        premier_mois = trimestre_index * 3 + 1
        debut = now.replace(month=premier_mois, day=1)
    else:  # "mois" (par défaut)
        debut = now.replace(day=1)

    return debut, now


def _datetime_bounds(date_debut, date_fin):
    """Convertit des bornes de date locales en bornes datetime aware,
    en évitant les lookups `__date` (nécessitent CONVERT_TZ côté MySQL,
    indisponible si les tables de fuseaux horaires ne sont pas chargées)."""
    debut_dt = timezone.make_aware(datetime.datetime.combine(date_debut, datetime.time.min))
    fin_dt = timezone.make_aware(datetime.datetime.combine(date_fin, datetime.time.max))
    return debut_dt, fin_dt


class ReportingDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        periode = request.query_params.get("periode", "mois")
        if periode not in ("mois", "trimestre", "annee"):
            periode = "mois"
        date_debut, date_fin = _periode_bounds(periode)
        debut_dt, fin_dt = _datetime_bounds(date_debut, date_fin)

        essais_periode = Essai.objects.filter(created_at__range=(debut_dt, fin_dt))
        essais_resolus = essais_periode.filter(statut__in=["TERMINE", "VALIDE"])
        essais_valides = essais_periode.filter(statut="VALIDE")

        ca_periode = Facture.objects.filter(
            statut="PAYEE",
            date_paiement__range=(date_debut, date_fin),
        ).aggregate(total=Sum("montant_ttc"))["total"] or 0

        devis_periode = DemandeDevis.objects.filter(
            created_at__range=(debut_dt, fin_dt),
            statut__in=["ACCEPTEE", "REFUSEE"],
        )
        devis_acceptees = devis_periode.filter(statut="ACCEPTEE")

        taux_conformite = (
            round(essais_valides.count() / essais_resolus.count() * 100)
            if essais_resolus.count()
            else 0
        )
        satisfaction = (
            round(devis_acceptees.count() / devis_periode.count() * 100)
            if devis_periode.count()
            else 0
        )

        rapports = Rapport.objects.all()
        data = {
            "periode": periode,
            "date_debut": date_debut,
            "date_fin": date_fin,
            "essais_ce_mois": essais_periode.count(),
            "ca_du_mois": ca_periode,
            "taux_conformite": taux_conformite,
            "satisfaction": satisfaction,
            "total_rapports": rapports.count(),
            "par_type": list(
                rapports.values("type_rapport").annotate(total=Count("id"))
            ),
        }
        return Response(data)


class RapportListView(generics.ListAPIView):
    queryset = Rapport.objects.all().order_by("-date_creation")
    serializer_class = RapportSerializer
    permission_classes = [permissions.IsAuthenticated]


class RapportGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, type_rapport):
        # Endpoint générique qui enregistre juste la demande de rapport
        titre = request.data.get("titre") or f"Rapport {type_rapport}"
        params = request.data.get("params") or {}
        rapport = Rapport.objects.create(
            type_rapport=type_rapport,
            titre=titre,
            parametres=params,
            cree_par=request.user,
        )
        serializer = RapportSerializer(rapport)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def compute_rapports_essais_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI des rapports d'essais."""
    rapports = RapportEssai.objects.all()
    if date_debut and date_fin:
        rapports = rapports.filter(date_creation__date__range=(date_debut, date_fin))

    valides = rapports.filter(statut__in=["VALIDE", "SIGNE"])
    en_attente = rapports.filter(statut="EN_ATTENTE_VALIDATION")

    valides_avec_dates = rapports.filter(date_soumission__isnull=False, date_validation__isnull=False)
    temps_moyen_validation = None
    if valides_avec_dates.exists():
        delais = [(r.date_validation - r.date_soumission).days for r in valides_avec_dates]
        temps_moyen_validation = round(sum(delais) / len(delais), 1)

    rapports_avec_soumission = rapports.filter(
        date_soumission__isnull=False, essai__date_fin__isnull=False
    ).select_related("essai")
    delais_remise = [(r.date_soumission - r.essai.date_fin).days for r in rapports_avec_soumission]
    delai_moyen_remise = round(sum(delais_remise) / len(delais_remise), 1) if delais_remise else None

    rapports_avec_delai_reglementaire = rapports_avec_soumission.filter(
        delai_reglementaire_jours__isnull=False
    )
    nb_dans_les_delais = sum(
        1 for r in rapports_avec_delai_reglementaire
        if (r.date_soumission - r.essai.date_fin).days <= r.delai_reglementaire_jours
    )
    taux_remise_delais = (
        round(nb_dans_les_delais / rapports_avec_delai_reglementaire.count() * 100, 1)
        if rapports_avec_delai_reglementaire.count() else None
    )

    return {
        "nombre_rapports_generes": rapports.count(),
        "nombre_rapports_valides": valides.count(),
        "nombre_rapports_en_attente_validation": en_attente.count(),
        "temps_moyen_validation_jours": temps_moyen_validation,
        "nombre_rapports_corriges": rapports.filter(statut="CORRIGE").count(),
        "delai_moyen_remise_jours": delai_moyen_remise,
        "taux_remise_dans_les_delais": taux_remise_delais,
        "nombre_rapports_signes_electroniquement": rapports.filter(signe_electroniquement=True).count(),
    }


class RapportEssaiViewSet(viewsets.ModelViewSet):
    queryset = RapportEssai.objects.select_related("essai", "valide_par").all()
    serializer_class = RapportEssaiSerializer
    permission_classes = [permissions.IsAuthenticated]


class RapportsEssaisKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_rapports_essais_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
