from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CompteComptableViewSet,
    EcritureComptableViewSet,
    EcrituresKPIView,
    JournalComptableViewSet,
)

router = DefaultRouter()
router.register(r"comptes", CompteComptableViewSet, basename="compta-compte-comptable")
router.register(r"journaux", JournalComptableViewSet, basename="compta-journal")
router.register(r"ecritures", EcritureComptableViewSet, basename="compta-ecriture")

urlpatterns = [
    path("kpis/", EcrituresKPIView.as_view(), name="compta-ecritures-kpis"),
    path("", include(router.urls)),
]
