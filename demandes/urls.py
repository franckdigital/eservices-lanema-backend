from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DemandeDevisViewSet, DemandesDashboardStatsView, TypesAnalyseView, DemandesSimpleView


router = DefaultRouter()
router.register(r"devis", DemandeDevisViewSet, basename="demande-devis")


urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", DemandesDashboardStatsView.as_view(), name="demandes-dashboard-stats"),
    path("types-analyse/", TypesAnalyseView.as_view(), name="types-analyse"),
    path("demandes-simple/", DemandesSimpleView.as_view(), name="demandes-simple"),
]
