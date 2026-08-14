from django.urls import path

from .views import DashboardAgentComptableTresorView, DashboardComptabiliteView

urlpatterns = [
    path("dashboard/", DashboardComptabiliteView.as_view(), name="comptabilite-dashboard"),
    path(
        "dashboard/agent-comptable-tresor/",
        DashboardAgentComptableTresorView.as_view(),
        name="comptabilite-dashboard-agent-comptable-tresor",
    ),
]
