from django.urls import path

from .views import (
    DashboardDAEChefAtelierView,
    DashboardDAEDirecteurView,
    DashboardDAETechnicienView,
    DashboardDAEView,
    HistoriqueActionDAEListView,
    PieceJointeDAEListCreateView,
)

urlpatterns = [
    path("dashboard/", DashboardDAEView.as_view(), name="aero-dashboard"),
    path("dashboard/directeur/", DashboardDAEDirecteurView.as_view(), name="aero-dashboard-directeur"),
    path("dashboard/chef-atelier/", DashboardDAEChefAtelierView.as_view(), name="aero-dashboard-chef-atelier"),
    path("dashboard/technicien/", DashboardDAETechnicienView.as_view(), name="aero-dashboard-technicien"),
    path("historique/", HistoriqueActionDAEListView.as_view(), name="aero-historique"),
    path("pieces-jointes/", PieceJointeDAEListCreateView.as_view(), name="aero-pieces-jointes"),
]
