from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CompteBancaireViewSet,
    MouvementBancaireViewSet,
    RapprochementBancaireViewSet,
    TresorerieKPIView,
)

router = DefaultRouter()
router.register(r"comptes", CompteBancaireViewSet, basename="compta-compte-bancaire")
router.register(r"mouvements", MouvementBancaireViewSet, basename="compta-mouvement-bancaire")
router.register(r"rapprochements", RapprochementBancaireViewSet, basename="compta-rapprochement")

urlpatterns = [
    path("kpis/", TresorerieKPIView.as_view(), name="compta-tresorerie-kpis"),
    path("", include(router.urls)),
]
