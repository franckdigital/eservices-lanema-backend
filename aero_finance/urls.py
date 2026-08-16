from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BonCommandeDAEViewSet, DevisDAEViewSet, FactureDAEViewSet, FinanciersKPIView

router = DefaultRouter()
router.register(r"devis", DevisDAEViewSet, basename="aero-devis")
router.register(r"bons-commande", BonCommandeDAEViewSet, basename="aero-bon-commande")
router.register(r"factures", FactureDAEViewSet, basename="aero-facture")

urlpatterns = [
    path("kpis/", FinanciersKPIView.as_view(), name="aero-financiers-kpis"),
    path("", include(router.urls)),
]
