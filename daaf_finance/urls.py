from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BudgetViewSet, DepenseViewSet, EcritureComptableViewSet, FinanceKPIView, RecetteViewSet

router = DefaultRouter()
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(r"ecritures", EcritureComptableViewSet, basename="ecriture-comptable")
router.register(r"recettes", RecetteViewSet, basename="recette")
router.register(r"depenses", DepenseViewSet, basename="depense")

urlpatterns = [
    path("kpis/", FinanceKPIView.as_view(), name="daaf-finance-kpis"),
    path("", include(router.urls)),
]
