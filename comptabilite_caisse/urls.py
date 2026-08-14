from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CaisseKPIView, CaisseViewSet, MouvementCaisseViewSet

router = DefaultRouter()
router.register(r"caisses", CaisseViewSet, basename="compta-caisse")
router.register(r"mouvements", MouvementCaisseViewSet, basename="compta-mouvement-caisse")

urlpatterns = [
    path("kpis/", CaisseKPIView.as_view(), name="compta-caisse-kpis"),
    path("", include(router.urls)),
]
