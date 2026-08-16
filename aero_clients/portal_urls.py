from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .portal_views import (
    ClientPortalAeronefViewSet,
    ClientPortalDashboardView,
    ClientPortalDemandeViewSet,
    ClientPortalFactureViewSet,
    ClientPortalLoginView,
    ClientPortalOrdreTravailView,
    ClientPortalProfileView,
    ClientPortalReclamationViewSet,
    ClientPortalRegisterView,
    ClientPortalSatisfactionView,
)

router = DefaultRouter()
router.register(r"aeronefs", ClientPortalAeronefViewSet, basename="portal-aeronef")
router.register(r"demandes", ClientPortalDemandeViewSet, basename="portal-demande")
router.register(r"ordres-travail", ClientPortalOrdreTravailView, basename="portal-ordre-travail")
router.register(r"factures", ClientPortalFactureViewSet, basename="portal-facture")
router.register(r"reclamations", ClientPortalReclamationViewSet, basename="portal-reclamation")

urlpatterns = [
    path("auth/register/", ClientPortalRegisterView.as_view(), name="portal-register"),
    path("auth/login/", ClientPortalLoginView.as_view(), name="portal-login"),
    path("auth/profile/", ClientPortalProfileView.as_view(), name="portal-profile"),
    path("dashboard/", ClientPortalDashboardView.as_view(), name="portal-dashboard"),
    path("satisfactions/", ClientPortalSatisfactionView.as_view(), name="portal-satisfactions"),
    path("satisfactions/<int:pk>/soumettre/", ClientPortalSatisfactionView.as_view(), name="portal-satisfaction-submit"),
    path("", include(router.urls)),
]
