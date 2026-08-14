from django.urls import path

from .views import (
    DashboardDEADGView,
    DashboardDEALaboView,
    DashboardDEAQualiteResponsableView,
    DashboardDEATechnicienView,
    DashboardDEAView,
)

urlpatterns = [
    path("dashboard/", DashboardDEAView.as_view(), name="dea-dashboard"),
    path("dashboard/dg/", DashboardDEADGView.as_view(), name="dea-dashboard-dg"),
    path("dashboard/labo/", DashboardDEALaboView.as_view(), name="dea-dashboard-labo"),
    path("dashboard/technicien/", DashboardDEATechnicienView.as_view(), name="dea-dashboard-technicien"),
    path(
        "dashboard/qualite-responsable/",
        DashboardDEAQualiteResponsableView.as_view(),
        name="dea-dashboard-qualite-responsable",
    ),
]
