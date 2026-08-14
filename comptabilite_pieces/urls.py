from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PieceComptableViewSet, PiecesKPIView

router = DefaultRouter()
router.register(r"pieces", PieceComptableViewSet, basename="compta-piece")

urlpatterns = [
    path("kpis/", PiecesKPIView.as_view(), name="compta-pieces-kpis"),
    path("", include(router.urls)),
]
