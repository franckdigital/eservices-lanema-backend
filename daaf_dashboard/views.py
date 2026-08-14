from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views_kpi_rh import compute_rh_kpis
from daaf_achats.views import compute_achats_kpis
from daaf_finance.models import Budget
from daaf_finance.views import compute_finance_kpis
from daaf_moyens_generaux.views import compute_moyens_generaux_kpis
from daaf_stock.views import compute_stock_kpis
from dg_patrimoine.views import compute_patrimoine_kpis


def _alertes_budgetaires():
    depassements = []
    for budget in Budget.objects.select_related("direction").filter(montant_engage__gt=0):
        if budget.montant_prevu and budget.montant_engage > budget.montant_prevu:
            depassements.append({
                "direction": budget.direction.nom if budget.direction else None,
                "annee": budget.annee,
                "categorie": budget.categorie,
                "montant_prevu": float(budget.montant_prevu),
                "montant_engage": float(budget.montant_engage),
                "depassement": float(budget.montant_engage - budget.montant_prevu),
            })
    return depassements


def _indice_global_performance(finance, achats, rh, moyens_generaux, patrimoine):
    """Moyenne ponderee simple, meme principe que le score global de
    dg_dashboard : execution budgetaire 30%, encaissement 25%, presence RH
    25%, disponibilite parc/patrimoine 20%. Ponderation documentee ici,
    ajustable si besoin."""
    composantes = [
        (finance.get("taux_execution_budgetaire"), 0.30),
        (finance.get("taux_encaissement"), 0.25),
        (rh.get("taux_presence"), 0.25),
        (moyens_generaux.get("disponibilite_parc_automobile") or patrimoine.get("taux_disponibilite_equipements"), 0.20),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    if not total_poids:
        return None
    score = sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids
    return round(score, 1)


class DashboardDAAFView(APIView):
    """Tableau de bord decisionnel de la DAAF : agrege Finance/Budget/
    Comptabilite/Tresorerie/Recettes/Depenses, Achats, RH, Patrimoine, Moyens
    Generaux et Stocks, plus les alertes de depassement budgetaire et un
    indice global de performance de la DAAF."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        finance = compute_finance_kpis(date_debut, date_fin)
        achats = compute_achats_kpis(date_debut, date_fin)
        rh = compute_rh_kpis(date_debut, date_fin)
        patrimoine = compute_patrimoine_kpis(date_debut, date_fin)
        moyens_generaux = compute_moyens_generaux_kpis(date_debut, date_fin)
        stock = compute_stock_kpis(date_debut, date_fin)

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "indice_global_performance_daaf": _indice_global_performance(
                finance, achats, rh, moyens_generaux, patrimoine
            ),
            "alertes_depassement_budgetaire": _alertes_budgetaires(),
            "finance": finance,
            "achats": achats,
            "rh": rh,
            "patrimoine": patrimoine,
            "moyens_generaux": moyens_generaux,
            "stock": stock,
        })
