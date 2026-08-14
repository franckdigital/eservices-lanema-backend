from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Batiment, InterventionTechnique, PanneVehicule, ReservationSalle, Salle, Vehicule
from .serializers import (
    BatimentSerializer,
    InterventionTechniqueSerializer,
    PanneVehiculeSerializer,
    ReservationSalleSerializer,
    SalleSerializer,
    VehiculeSerializer,
)


def _business_days(date_debut, date_fin):
    jours = 0
    current = date_debut
    while current <= date_fin:
        if current.weekday() < 5:
            jours += 1
        current += timedelta(days=1)
    return jours


def compute_moyens_generaux_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Moyens Generaux. Reutilisable directement par le
    tableau de bord DAAF."""
    from core.models import MissionRH
    from daaf_finance.models import Depense

    today = timezone.now().date()
    if date_debut and date_fin:
        periode_debut, periode_fin = date_debut, date_fin
        if isinstance(periode_debut, str):
            periode_debut = timezone.datetime.strptime(periode_debut, "%Y-%m-%d").date()
        if isinstance(periode_fin, str):
            periode_fin = timezone.datetime.strptime(periode_fin, "%Y-%m-%d").date()
    else:
        periode_debut, periode_fin = today.replace(day=1), today

    vehicules = Vehicule.objects.all()
    total_vehicules = vehicules.count()
    nb_disponibles = vehicules.filter(statut="DISPONIBLE").count()
    taux_disponibilite_parc = round(nb_disponibles / total_vehicules * 100, 1) if total_vehicules else None

    pannes = PanneVehicule.objects.filter(date_panne__range=(periode_debut, periode_fin))
    cout_maintenance_vehicules = pannes.aggregate(t=Sum("cout"))["t"] or 0

    batiments = Batiment.objects.all()
    total_batiments = batiments.count()
    nb_batiments_disponibles = batiments.filter(disponible=True).count()
    taux_disponibilite_batiments = (
        round(nb_batiments_disponibles / total_batiments * 100, 1) if total_batiments else None
    )

    nb_interventions = InterventionTechnique.objects.filter(
        date_intervention__range=(periode_debut, periode_fin)
    ).count()

    nb_salles = Salle.objects.count()
    reservations = ReservationSalle.objects.filter(
        date_debut__date__range=(periode_debut, periode_fin)
    )
    heures_reservees = sum(
        (r.date_fin - r.date_debut).total_seconds() / 3600 for r in reservations
    )
    jours_ouvres = _business_days(periode_debut, periode_fin)
    capacite_theorique_heures = nb_salles * jours_ouvres * 8
    taux_occupation_salles = (
        round(heures_reservees / capacite_theorique_heures * 100, 1) if capacite_theorique_heures else None
    )

    nb_missions = MissionRH.objects.filter(
        date_debut__range=(periode_debut, periode_fin)
    ).exclude(statut__in=["rejetee"]).count()

    consommation_carburant = Depense.objects.filter(
        categorie="CARBURANT", date_engagement__range=(periode_debut, periode_fin)
    ).aggregate(t=Sum("montant"))["t"] or 0

    return {
        "disponibilite_parc_automobile": taux_disponibilite_parc,
        "nombre_missions_effectuees": nb_missions,
        "consommation_carburant": float(consommation_carburant),
        "nombre_pannes_vehicules": pannes.count(),
        "cout_maintenance_vehicules": float(cout_maintenance_vehicules),
        "taux_occupation_salles": taux_occupation_salles,
        "taux_occupation_salles_note": "Approximation : heures reservees / (nb salles x jours ouvres x 8h).",
        "disponibilite_batiments": taux_disponibilite_batiments,
        "nombre_interventions_techniques": nb_interventions,
    }


class VehiculeViewSet(viewsets.ModelViewSet):
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer
    permission_classes = [permissions.IsAuthenticated]


class PanneVehiculeViewSet(viewsets.ModelViewSet):
    queryset = PanneVehicule.objects.select_related("vehicule").all()
    serializer_class = PanneVehiculeSerializer
    permission_classes = [permissions.IsAuthenticated]


class BatimentViewSet(viewsets.ModelViewSet):
    queryset = Batiment.objects.select_related("site").all()
    serializer_class = BatimentSerializer
    permission_classes = [permissions.IsAuthenticated]


class SalleViewSet(viewsets.ModelViewSet):
    queryset = Salle.objects.select_related("batiment").all()
    serializer_class = SalleSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReservationSalleViewSet(viewsets.ModelViewSet):
    queryset = ReservationSalle.objects.select_related("salle").all()
    serializer_class = ReservationSalleSerializer
    permission_classes = [permissions.IsAuthenticated]


class InterventionTechniqueViewSet(viewsets.ModelViewSet):
    queryset = InterventionTechnique.objects.select_related("batiment").all()
    serializer_class = InterventionTechniqueSerializer
    permission_classes = [permissions.IsAuthenticated]


class MoyensGenerauxKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_moyens_generaux_kpis(date_debut, date_fin))
