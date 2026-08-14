from django.urls import path

from .views import (
    DashboardDFIRChefServiceFormationView,
    DashboardDFIRChefServiceRechercheInnovationView,
    DashboardDFIRDirecteurView,
    DashboardDFIRFormateurView,
    DashboardDFIRView,
)

urlpatterns = [
    path("dashboard/", DashboardDFIRView.as_view(), name="dfir-dashboard"),
    path("dashboard/directeur/", DashboardDFIRDirecteurView.as_view(), name="dfir-dashboard-directeur"),
    path(
        "dashboard/chef-service-formation/",
        DashboardDFIRChefServiceFormationView.as_view(),
        name="dfir-dashboard-chef-service-formation",
    ),
    path(
        "dashboard/chef-service-recherche-innovation/",
        DashboardDFIRChefServiceRechercheInnovationView.as_view(),
        name="dfir-dashboard-chef-service-recherche-innovation",
    ),
    path("dashboard/formateur/", DashboardDFIRFormateurView.as_view(), name="dfir-dashboard-formateur"),
]
