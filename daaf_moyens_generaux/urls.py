from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BatimentViewSet,
    InterventionTechniqueViewSet,
    MoyensGenerauxKPIView,
    PanneVehiculeViewSet,
    ReservationSalleViewSet,
    SalleViewSet,
    VehiculeViewSet,
)

router = DefaultRouter()
router.register(r"vehicules", VehiculeViewSet, basename="vehicule")
router.register(r"pannes", PanneVehiculeViewSet, basename="panne-vehicule")
router.register(r"batiments", BatimentViewSet, basename="batiment")
router.register(r"salles", SalleViewSet, basename="salle")
router.register(r"reservations-salles", ReservationSalleViewSet, basename="reservation-salle")
router.register(r"interventions", InterventionTechniqueViewSet, basename="intervention-technique")

urlpatterns = [
    path("kpis/", MoyensGenerauxKPIView.as_view(), name="daaf-moyens-generaux-kpis"),
    path("", include(router.urls)),
]
