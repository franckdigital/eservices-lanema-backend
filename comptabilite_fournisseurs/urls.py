from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FactureFournisseurViewSet,
    FournisseurComptableViewSet,
    FournisseursKPIView,
    PaiementFournisseurViewSet,
)

router = DefaultRouter()
router.register(r"fournisseurs", FournisseurComptableViewSet, basename="compta-fournisseur")
router.register(r"factures", FactureFournisseurViewSet, basename="compta-facture-fournisseur")
router.register(r"paiements", PaiementFournisseurViewSet, basename="compta-paiement-fournisseur")

urlpatterns = [
    path("kpis/", FournisseursKPIView.as_view(), name="compta-fournisseurs-kpis"),
    path("", include(router.urls)),
]
