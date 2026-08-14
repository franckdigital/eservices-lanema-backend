from django.urls import path

from .views import DashboardStatsView, DashboardKPIsView, DashboardActivitiesView

urlpatterns = [
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/kpis/', DashboardKPIsView.as_view(), name='dashboard-kpis'),
    path('dashboard/activities/', DashboardActivitiesView.as_view(), name='dashboard-activities'),
]
