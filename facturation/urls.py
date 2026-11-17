from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BonCommandeViewSet,
    CompteEmailLaboViewSet,
    DemandeAnalyseViewSet,
    FacturationStatsView,
    FactureViewSet,
    FinanciersKPIView,
    ProformaViewSet,
)


router = DefaultRouter()
router.register(r"factures", FactureViewSet, basename="facture")
router.register(r"proformas", ProformaViewSet, basename="proforma")
router.register(r"bons-commande", BonCommandeViewSet, basename="bon-commande")
router.register(r"demandes-analyses", DemandeAnalyseViewSet, basename="demande-analyse")
router.register(r"comptes-email", CompteEmailLaboViewSet, basename="compte-email-labo")


urlpatterns = [
    path("factures/stats/", FacturationStatsView.as_view(), name="facturation-factures-stats"),
    path("financiers/kpis/", FinanciersKPIView.as_view(), name="dea-financiers-kpis"),
    path("", include(router.urls)),
]
