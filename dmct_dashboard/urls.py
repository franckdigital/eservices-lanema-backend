from django.urls import path

from .views import (
    DashboardDMCTChefServiceView,
    DashboardDMCTDirecteurView,
    DashboardDMCTMetrologueView,
    DashboardDMCTView,
)

urlpatterns = [
    path("dashboard/", DashboardDMCTView.as_view(), name="dmct-dashboard"),
    path("dashboard/directeur/", DashboardDMCTDirecteurView.as_view(), name="dmct-dashboard-directeur"),
    path("dashboard/chef-service/", DashboardDMCTChefServiceView.as_view(), name="dmct-dashboard-chef-service"),
    path("dashboard/metrologue/", DashboardDMCTMetrologueView.as_view(), name="dmct-dashboard-metrologue"),
]
