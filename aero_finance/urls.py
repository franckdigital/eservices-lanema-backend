from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FactureDAEViewSet, FinanciersKPIView

router = DefaultRouter()
router.register(r"factures", FactureDAEViewSet, basename="aero-facture")

urlpatterns = [
    path("kpis/", FinanciersKPIView.as_view(), name="aero-financiers-kpis"),
    path("", include(router.urls)),
]
