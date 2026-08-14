from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActionCommunicationViewSet,
    CommunicationDashboardChefServiceView,
    CommunicationDashboardDirecteurView,
    CommunicationKPIView,
    PartenariatViewSet,
    ProspectViewSet,
    SatisfactionClientViewSet,
)

router = DefaultRouter()
router.register(r"actions", ActionCommunicationViewSet, basename="action-communication")
router.register(r"prospects", ProspectViewSet, basename="prospect")
router.register(r"partenariats", PartenariatViewSet, basename="partenariat")
router.register(r"satisfaction", SatisfactionClientViewSet, basename="satisfaction-client")

urlpatterns = [
    path("kpis/", CommunicationKPIView.as_view(), name="dg-communication-kpis"),
    path("dashboard/directeur/", CommunicationDashboardDirecteurView.as_view(), name="dg-communication-dashboard-directeur"),
    path("dashboard/chef-service/", CommunicationDashboardChefServiceView.as_view(), name="dg-communication-dashboard-chef-service"),
    path("", include(router.urls)),
]
