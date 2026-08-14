from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArticleStockViewSet, LotStockViewSet, MouvementStockAdminViewSet, StockKPIView

router = DefaultRouter()
router.register(r"articles", ArticleStockViewSet, basename="article-stock")
router.register(r"lots", LotStockViewSet, basename="lot-stock")
router.register(r"mouvements", MouvementStockAdminViewSet, basename="mouvement-stock-admin")

urlpatterns = [
    path("kpis/", StockKPIView.as_view(), name="daaf-stock-kpis"),
    path("", include(router.urls)),
]
