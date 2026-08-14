from django.urls import path

from .views import (
    DashboardDAEChefAtelierView,
    DashboardDAEDirecteurView,
    DashboardDAETechnicienView,
    DashboardDAEView,
)

urlpatterns = [
    path("dashboard/", DashboardDAEView.as_view(), name="aero-dashboard"),
    path("dashboard/directeur/", DashboardDAEDirecteurView.as_view(), name="aero-dashboard-directeur"),
    path("dashboard/chef-atelier/", DashboardDAEChefAtelierView.as_view(), name="aero-dashboard-chef-atelier"),
    path("dashboard/technicien/", DashboardDAETechnicienView.as_view(), name="aero-dashboard-technicien"),
]
