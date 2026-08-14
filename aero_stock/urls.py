from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MouvementPieceRechangeViewSet, PieceRechangeViewSet, StockKPIView

router = DefaultRouter()
router.register(r"pieces", PieceRechangeViewSet, basename="aero-piece")
router.register(r"mouvements", MouvementPieceRechangeViewSet, basename="aero-mouvement-piece")

urlpatterns = [
    path("kpis/", StockKPIView.as_view(), name="aero-stock-kpis"),
    path("", include(router.urls)),
]
