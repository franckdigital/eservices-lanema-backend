from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    AlerteViewSet,
    ArticleViewSet,
    EntrepotViewSet,
    EmplacementViewSet,
    LotViewSet,
    QuarantaineViewSet,
    ReceptionViewSet,
    StockDashboardStatsView,
    TransfertInterneViewSet,
    SortieStockViewSet,
    MouvementStockViewSet,
    StockStatistiquesView,
    MouvementsStatistiquesView,
    SortiesStatistiquesView,
    TableauBordCompletView,
    InventaireViewSet,
    LigneInventaireViewSet,
    DomaineViewSet,
    CategorieArticleViewSet,
    ReactifsKPIView,
)


router = DefaultRouter()
router.register(r"entrepots", EntrepotViewSet, basename="entrepot")
router.register(r"emplacements", EmplacementViewSet, basename="emplacement")
router.register(r"domaines", DomaineViewSet, basename="domaine")
router.register(r"categories", CategorieArticleViewSet, basename="categorie")
router.register(r"articles", ArticleViewSet, basename="article")
router.register(r"lots", LotViewSet, basename="lot")
router.register(r"alertes", AlerteViewSet, basename="alerte")
router.register(r"quarantaines", QuarantaineViewSet, basename="quarantaine")
router.register(r"receptions", ReceptionViewSet, basename="reception")
router.register(r"transferts", TransfertInterneViewSet, basename="transfertinterne")
router.register(r"sorties", SortieStockViewSet, basename="sortie")
router.register(r"mouvements", MouvementStockViewSet, basename="mouvement")
router.register(r"inventaires", InventaireViewSet, basename="inventaire")
router.register(r"lignes-inventaire", LigneInventaireViewSet, basename="ligne-inventaire")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", StockDashboardStatsView.as_view(), name="stock-dashboard-stats"),
    path("dashboard/complet/", TableauBordCompletView.as_view(), name="stock-dashboard-complet"),
    path("statistiques/stock/", StockStatistiquesView.as_view(), name="stock-statistiques"),
    path("statistiques/mouvements/", MouvementsStatistiquesView.as_view(), name="mouvements-statistiques"),
    path("statistiques/sorties/", SortiesStatistiquesView.as_view(), name="sorties-statistiques"),
    path("reactifs/kpis/", ReactifsKPIView.as_view(), name="dea-reactifs-kpis"),
]
