from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AchatsKPIView, BonCommandeViewSet, DemandeAchatViewSet, FournisseurViewSet, MarcheViewSet

router = DefaultRouter()
router.register(r"fournisseurs", FournisseurViewSet, basename="fournisseur")
router.register(r"demandes", DemandeAchatViewSet, basename="demande-achat")
router.register(r"bons-commande", BonCommandeViewSet, basename="bon-commande")
router.register(r"marches", MarcheViewSet, basename="marche")

urlpatterns = [
    path("kpis/", AchatsKPIView.as_view(), name="daaf-achats-kpis"),
    path("", include(router.urls)),
]
