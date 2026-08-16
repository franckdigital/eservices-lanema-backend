from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AeronefViewSet,
    ClientAeronautiqueViewSet,
    ClientsKPIView,
    DemandeDAEViewSet,
    ReclamationClientDAEViewSet,
    SatisfactionDAEPublicView,
    SatisfactionDAEViewSet,
)

router = DefaultRouter()
router.register(r"clients", ClientAeronautiqueViewSet, basename="aero-client")
router.register(r"aeronefs", AeronefViewSet, basename="aero-aeronef")
router.register(r"reclamations", ReclamationClientDAEViewSet, basename="aero-reclamation")
router.register(r"demandes", DemandeDAEViewSet, basename="aero-demande")
router.register(r"satisfaction", SatisfactionDAEViewSet, basename="aero-satisfaction")

urlpatterns = [
    path("kpis/", ClientsKPIView.as_view(), name="aero-clients-kpis"),
    path("satisfaction-publique/<uuid:token>/", SatisfactionDAEPublicView.as_view(), name="aero-satisfaction-publique"),
    path("", include(router.urls)),
]
