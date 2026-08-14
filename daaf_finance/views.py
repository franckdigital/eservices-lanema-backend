from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Budget, Depense, EcritureComptable, Recette
from .serializers import BudgetSerializer, DepenseSerializer, EcritureComptableSerializer, RecetteSerializer


def _budget_kpis():
    budgets = Budget.objects.all()
    prevu = budgets.aggregate(total=Sum("montant_prevu"))["total"] or 0
    engage = budgets.aggregate(total=Sum("montant_engage"))["total"] or 0
    realise = budgets.aggregate(total=Sum("montant_realise"))["total"] or 0
    revisions = budgets.aggregate(total=Sum("nombre_revisions"))["total"] or 0

    taux_execution = round(float(realise) / float(prevu) * 100, 1) if prevu else None
    taux_consommation = round(float(engage) / float(prevu) * 100, 1) if prevu else None

    return {
        "taux_execution_budgetaire": taux_execution,
        "taux_consommation_budget": taux_consommation,
        "budget_engage": float(engage),
        "budget_disponible": float(prevu) - float(engage),
        "ecart_previsionnel_realise": float(prevu) - float(realise),
        "nombre_revisions_budgetaires": revisions,
        "budget_prevu_total": float(prevu),
    }


def _comptabilite_kpis(date_debut=None, date_fin=None):
    ecritures = EcritureComptable.objects.all()
    if date_debut and date_fin:
        ecritures = ecritures.filter(date_ecriture__range=(date_debut, date_fin))

    total = ecritures.count()
    delais = [(e.created_at.date() - e.date_ecriture).days for e in ecritures]
    delai_moyen = round(sum(delais) / len(delais), 1) if delais else None
    nb_pieces = ecritures.exclude(piece_justificative="").values("piece_justificative").distinct().count()
    nb_erreurs = ecritures.filter(erreur=True).count()
    taux_erreurs = round(nb_erreurs / total * 100, 1) if total else None

    return {
        "nombre_ecritures_comptables": total,
        "delai_moyen_traitement_comptable_jours": delai_moyen,
        "nombre_pieces_comptables_traitees": nb_pieces,
        "taux_erreurs_comptables": taux_erreurs,
    }


def _recettes_kpis(date_debut=None, date_fin=None):
    recettes = Recette.objects.all()
    if date_debut and date_fin:
        recettes = recettes.filter(date_emission__range=(date_debut, date_fin))

    today = timezone.now().date()
    mois_courant_debut = today.replace(day=1)
    ca_mensuel = recettes.filter(date_emission__gte=mois_courant_debut).aggregate(t=Sum("montant"))["t"] or 0

    ca_par_direction = list(
        recettes.exclude(direction__isnull=True)
        .values("direction__nom")
        .annotate(total=Sum("montant"))
        .order_by("-total")
    )
    ca_par_prestation = list(
        recettes.exclude(type_prestation="")
        .values("type_prestation")
        .annotate(total=Sum("montant"))
        .order_by("-total")
    )
    recettes_par_client = list(
        recettes.exclude(client_nom="")
        .values("client_nom")
        .annotate(total=Sum("montant"))
        .order_by("-total")[:10]
    )

    nb_emises = recettes.count()
    nb_encaissees = recettes.filter(statut="ENCAISSEE").count()
    taux_encaissement = round(nb_encaissees / nb_emises * 100, 1) if nb_emises else None

    montant_impayes = recettes.filter(statut="IMPAYEE").aggregate(t=Sum("montant"))["t"] or 0
    creances_souffrance = recettes.filter(
        statut="IMPAYEE", date_emission__lt=today - timezone.timedelta(days=30)
    ).aggregate(t=Sum("montant"))["t"] or 0

    encaissees = recettes.filter(statut="ENCAISSEE", date_encaissement__isnull=False)
    delai_moyen_encaissement = None
    if encaissees.exists():
        delais = [(r.date_encaissement - r.date_emission).days for r in encaissees]
        delai_moyen_encaissement = round(sum(delais) / len(delais), 1)

    # Évolution sur les 6 derniers mois calendaires
    evolution_mensuelle = list(
        recettes.filter(date_emission__gte=today.replace(day=1) - timezone.timedelta(days=180))
        .annotate(mois=TruncMonth("date_emission"))
        .values("mois")
        .annotate(total=Sum("montant"))
        .order_by("mois")
    )
    for entry in evolution_mensuelle:
        entry["mois"] = entry["mois"].strftime("%Y-%m") if entry["mois"] else None

    return {
        "chiffre_affaires_mensuel": float(ca_mensuel),
        "chiffre_affaires_par_direction": ca_par_direction,
        "chiffre_affaires_par_prestation": ca_par_prestation,
        "nombre_factures_emises": nb_emises,
        "nombre_factures_encaissees": nb_encaissees,
        "taux_encaissement": taux_encaissement,
        "taux_recouvrement": taux_encaissement,
        "montant_impayes": float(montant_impayes),
        "creances_en_souffrance": float(creances_souffrance),
        "delai_moyen_encaissement_jours": delai_moyen_encaissement,
        "recettes_par_client": recettes_par_client,
        "evolution_mensuelle_recettes": evolution_mensuelle,
    }


def _depenses_kpis(date_debut=None, date_fin=None, budget_prevu_total=0):
    depenses = Depense.objects.all()
    if date_debut and date_fin:
        depenses = depenses.filter(date_engagement__range=(date_debut, date_fin))

    depenses_par_direction = list(
        depenses.exclude(direction__isnull=True)
        .values("direction__nom")
        .annotate(total=Sum("montant"))
        .order_by("-total")
    )

    def total_categorie(cat):
        return float(depenses.filter(categorie=cat).aggregate(t=Sum("montant"))["t"] or 0)

    depenses_prestation = list(
        depenses.exclude(prestation_associee="")
        .values("prestation_associee")
        .annotate(moyenne=Sum("montant") / Count("id"))
        .order_by("-moyenne")
    )
    depenses_site = list(
        depenses.exclude(site__isnull=True)
        .values("site__nom")
        .annotate(moyenne=Sum("montant") / Count("id"))
        .order_by("-moyenne")
    )

    total_depenses = depenses.aggregate(t=Sum("montant"))["t"] or 0
    taux_maitrise = (
        round(float(total_depenses) / float(budget_prevu_total) * 100, 1) if budget_prevu_total else None
    )

    payees = depenses.filter(statut="PAYEE", date_paiement__isnull=False)
    delai_moyen_paiement = None
    if payees.exists():
        delais = [(d.date_paiement - d.date_engagement).days for d in payees]
        delai_moyen_paiement = round(sum(delais) / len(delais), 1)

    dettes_fournisseurs = list(
        depenses.filter(statut__in=["ENGAGEE", "IMPAYEE"])
        .exclude(fournisseur_nom="")
        .values("fournisseur_nom")
        .annotate(total=Sum("montant"))
        .order_by("-total")
    )

    return {
        "depenses_par_direction": depenses_par_direction,
        "depenses_fonctionnement": total_categorie("FONCTIONNEMENT"),
        "depenses_investissement": total_categorie("INVESTISSEMENT"),
        "cout_moyen_par_prestation": depenses_prestation,
        "cout_moyen_par_site": depenses_site,
        "taux_maitrise_depenses": taux_maitrise,
        "depenses_carburant": total_categorie("CARBURANT"),
        "depenses_electricite_eau": total_categorie("ELECTRICITE_EAU"),
        "depenses_telecommunications": total_categorie("TELECOM"),
        "dettes_fournisseurs": dettes_fournisseurs,
        "total_depenses": float(total_depenses),
        "delai_moyen_paiement_fournisseurs_jours": delai_moyen_paiement,
    }


def _tresorerie_kpis(date_debut=None, date_fin=None):
    recettes = Recette.objects.filter(statut="ENCAISSEE")
    depenses = Depense.objects.filter(statut="PAYEE")
    if date_debut and date_fin:
        recettes_periode = recettes.filter(date_encaissement__range=(date_debut, date_fin))
        depenses_periode = depenses.filter(date_paiement__range=(date_debut, date_fin))
    else:
        recettes_periode = recettes
        depenses_periode = depenses

    total_encaisse = recettes.aggregate(t=Sum("montant"))["t"] or 0
    total_paye = depenses.aggregate(t=Sum("montant"))["t"] or 0
    flux_entrants = recettes_periode.aggregate(t=Sum("montant"))["t"] or 0
    flux_sortants = depenses_periode.aggregate(t=Sum("montant"))["t"] or 0

    depenses_fonctionnement_payees = depenses_periode.filter(categorie="FONCTIONNEMENT").aggregate(
        t=Sum("montant")
    )["t"] or 0
    caf = float(flux_entrants) - float(depenses_fonctionnement_payees)

    return {
        "solde_tresorerie": float(total_encaisse) - float(total_paye),
        "flux_tresorerie_entrants": float(flux_entrants),
        "flux_tresorerie_sortants": float(flux_sortants),
        "capacite_autofinancement": caf,
        "capacite_autofinancement_note": (
            "Approximation : flux entrants encaisses moins depenses de fonctionnement payees sur la periode."
        ),
    }


def compute_finance_kpis(date_debut=None, date_fin=None):
    """Calcule les 40 KPI Finance/Budget/Comptabilite/Tresorerie/Recettes/Depenses.
    Reutilisable directement par le tableau de bord DAAF."""
    from dg_patrimoine.views import compute_patrimoine_kpis

    budget = _budget_kpis()
    comptabilite = _comptabilite_kpis(date_debut, date_fin)
    recettes = _recettes_kpis(date_debut, date_fin)
    depenses = _depenses_kpis(date_debut, date_fin, budget_prevu_total=budget["budget_prevu_total"])
    tresorerie = _tresorerie_kpis(date_debut, date_fin)

    patrimoine = compute_patrimoine_kpis(date_debut, date_fin)

    result = {}
    result.update(budget)
    result.update(comptabilite)
    result.update(recettes)
    result.update(depenses)
    result.update(tresorerie)
    result["cout_maintenance_equipements"] = patrimoine.get("cout_annuel_maintenance")
    return result


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related("direction").all()
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]


class EcritureComptableViewSet(viewsets.ModelViewSet):
    queryset = EcritureComptable.objects.all()
    serializer_class = EcritureComptableSerializer
    permission_classes = [permissions.IsAuthenticated]


class RecetteViewSet(viewsets.ModelViewSet):
    queryset = Recette.objects.select_related("direction").all()
    serializer_class = RecetteSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepenseViewSet(viewsets.ModelViewSet):
    queryset = Depense.objects.select_related("direction", "site").all()
    serializer_class = DepenseSerializer
    permission_classes = [permissions.IsAuthenticated]


class FinanceKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_finance_kpis(date_debut, date_fin))
