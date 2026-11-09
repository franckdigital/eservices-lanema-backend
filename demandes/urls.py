from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CreneauDisponibiliteViewSet,
    DelaiActuelView,
    DemandeDevisViewSet,
    DemandesDashboardStatsView,
    DemandesSimpleView,
    PublicDevisCreateView,
    SousTraitantPartenaireViewSet,
    TypesAnalyseView,
)


router = DefaultRouter()
router.register(r"devis", DemandeDevisViewSet, basename="demande-devis")
router.register(r"creneaux-disponibilite", CreneauDisponibiliteViewSet, basename="creneau-disponibilite")
router.register(r"sous-traitants", SousTraitantPartenaireViewSet, basename="sous-traitant")


urlpatterns = [
    path("devis/public/", PublicDevisCreateView.as_view(), name="demande-devis-public"),
    path("delai-actuel/", DelaiActuelView.as_view(), name="demande-devis-delai-actuel"),
    path("", include(router.urls)),
    path("dashboard/stats/", DemandesDashboardStatsView.as_view(), name="demandes-dashboard-stats"),
    path("types-analyse/", TypesAnalyseView.as_view(), name="types-analyse"),
    path("demandes-simple/", DemandesSimpleView.as_view(), name="demandes-simple"),
]
