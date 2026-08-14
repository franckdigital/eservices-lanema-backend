from .modules.entrepots import EntrepotViewSet, EmplacementViewSet
from .modules.articles import ArticleViewSet
from .modules.lots import LotViewSet
from .modules.alertes import AlerteViewSet
from .modules.quarantaines import QuarantaineViewSet
from .modules.receptions import ReceptionViewSet
from .modules.transferts import TransfertInterneViewSet
from .modules.dashboard import StockDashboardStatsView
from .modules.sorties import SortieStockViewSet
from .modules.mouvements import MouvementStockViewSet
from .modules.statistiques import (
    StockStatistiquesView,
    MouvementsStatistiquesView,
    SortiesStatistiquesView,
    TableauBordCompletView,
)
from .modules.inventaires import InventaireViewSet, LigneInventaireViewSet
from .modules.domaines import DomaineViewSet, CategorieArticleViewSet
from .modules.reactifs_kpi import ReactifsKPIView
