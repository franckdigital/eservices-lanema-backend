from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BatterieAeronefViewSet,
    BatteriesKPIView,
    EquipementAeronautiqueViewSet,
    InspectionRoueViewSet,
    InterventionTechniqueViewSet,
    MaintenanceKPIView,
    OrdreTravailViewSet,
    RoueAeronefViewSet,
    RouesKPIView,
    TestBatterieViewSet,
)

router = DefaultRouter()
router.register(r"ordres-travail", OrdreTravailViewSet, basename="aero-ordre-travail")
router.register(r"interventions", InterventionTechniqueViewSet, basename="aero-intervention")
router.register(r"equipements", EquipementAeronautiqueViewSet, basename="aero-equipement")
router.register(r"roues", RoueAeronefViewSet, basename="aero-roue")
router.register(r"inspections-roues", InspectionRoueViewSet, basename="aero-inspection-roue")
router.register(r"batteries", BatterieAeronefViewSet, basename="aero-batterie")
router.register(r"tests-batteries", TestBatterieViewSet, basename="aero-test-batterie")

urlpatterns = [
    path("kpis/", MaintenanceKPIView.as_view(), name="aero-maintenance-kpis"),
    path("kpis/roues/", RouesKPIView.as_view(), name="aero-roues-kpis"),
    path("kpis/batteries/", BatteriesKPIView.as_view(), name="aero-batteries-kpis"),
    path("", include(router.urls)),
]
