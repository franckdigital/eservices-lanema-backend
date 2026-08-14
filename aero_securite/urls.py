from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ControleReglementaireViewSet,
    EcartReglementaireViewSet,
    FormationSecuriteViewSet,
    IncidentTechniqueViewSet,
    RapportSecuriteViewSet,
    SecuriteKPIView,
)

router = DefaultRouter()
router.register(r"incidents", IncidentTechniqueViewSet, basename="aero-incident")
router.register(r"ecarts-reglementaires", EcartReglementaireViewSet, basename="aero-ecart-reglementaire")
router.register(r"rapports", RapportSecuriteViewSet, basename="aero-rapport-securite")
router.register(r"controles-reglementaires", ControleReglementaireViewSet, basename="aero-controle-reglementaire")
router.register(r"formations", FormationSecuriteViewSet, basename="aero-formation-securite")

urlpatterns = [
    path("kpis/", SecuriteKPIView.as_view(), name="aero-securite-kpis"),
    path("", include(router.urls)),
]
