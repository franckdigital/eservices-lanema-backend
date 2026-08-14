from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CollaborationRechercheViewSet,
    ProjetRechercheViewSet,
    PublicationScientifiqueViewSet,
    RapportRechercheViewSet,
    RechercheKPIView,
    RecommandationRechercheViewSet,
)

router = DefaultRouter()
router.register(r"projets", ProjetRechercheViewSet, basename="dfir-projet-recherche")
router.register(r"publications", PublicationScientifiqueViewSet, basename="dfir-publication")
router.register(r"rapports", RapportRechercheViewSet, basename="dfir-rapport-recherche")
router.register(r"recommandations", RecommandationRechercheViewSet, basename="dfir-recommandation")
router.register(r"collaborations", CollaborationRechercheViewSet, basename="dfir-collaboration")

urlpatterns = [
    path("kpis/", RechercheKPIView.as_view(), name="dfir-recherche-kpis"),
    path("", include(router.urls)),
]
