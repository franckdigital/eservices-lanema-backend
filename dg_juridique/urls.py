from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AvisJuridiqueViewSet,
    ContentieuxViewSet,
    ContratViewSet,
    DossierJuridiqueViewSet,
    JuridiqueDashboardChefServiceView,
    JuridiqueDashboardDirecteurView,
    JuridiqueKPIView,
    ProcedureDisciplinaireViewSet,
    TexteReglementaireViewSet,
)

router = DefaultRouter()
router.register(r"dossiers", DossierJuridiqueViewSet, basename="dossier-juridique")
router.register(r"contrats", ContratViewSet, basename="contrat")
router.register(r"contentieux", ContentieuxViewSet, basename="contentieux")
router.register(r"avis", AvisJuridiqueViewSet, basename="avis-juridique")
router.register(r"procedures-disciplinaires", ProcedureDisciplinaireViewSet, basename="procedure-disciplinaire")
router.register(r"textes-reglementaires", TexteReglementaireViewSet, basename="texte-reglementaire")

urlpatterns = [
    path("kpis/", JuridiqueKPIView.as_view(), name="dg-juridique-kpis"),
    path("dashboard/directeur/", JuridiqueDashboardDirecteurView.as_view(), name="dg-juridique-dashboard-directeur"),
    path("dashboard/chef-service/", JuridiqueDashboardChefServiceView.as_view(), name="dg-juridique-dashboard-chef-service"),
    path("", include(router.urls)),
]
