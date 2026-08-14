from django.urls import path

from .views import DashboardDAAFView

urlpatterns = [
    path("dashboard/", DashboardDAAFView.as_view(), name="daaf-dashboard"),
]
