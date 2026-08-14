from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from comptabilite_caisse.views import compute_caisse_kpis
from comptabilite_ecritures.views import compute_ecritures_kpis
from comptabilite_fournisseurs.models import FactureFournisseur
from comptabilite_fournisseurs.views import compute_fournisseurs_kpis
from comptabilite_pieces.views import compute_pieces_kpis
from comptabilite_tresorerie.models import MouvementBancaire
from comptabilite_tresorerie.views import compute_tresorerie_kpis
from demandes.models import DemandeDevis
from facturation.models import BonCommande, DemandeAnalyse, Facture
from facturation.views import compute_financiers_kpis as compute_facturation_labo_kpis


def compute_facturation_kpis(date_debut=None, date_fin=None):
    """Reprend les KPI financiers du labo (facturation.compute_financiers_kpis,
    pas de recalcul) et y ajoute un comptage devis/commandes/demandes
    d'analyses pour la vue comptabilite."""
    financiers_labo = compute_facturation_labo_kpis(date_debut, date_fin)

    devis = DemandeDevis.objects.all()
    commandes = BonCommande.objects.all()
    demandes_analyses = DemandeAnalyse.objects.all()
    if date_debut and date_fin:
        devis = devis.filter(created_at__date__range=(date_debut, date_fin))
        commandes = commandes.filter(date_emission__range=(date_debut, date_fin))
        demandes_analyses = demandes_analyses.filter(date_creation__date__range=(date_debut, date_fin))

    return {
        **financiers_labo,
        "nombre_devis": devis.count(),
        "nombre_devis_acceptes": devis.filter(statut="ACCEPTEE").count(),
        "nombre_commandes": commandes.count(),
        "nombre_commandes_signees": commandes.filter(statut="SIGNE_CLIENT").count(),
        "nombre_demandes_analyses": demandes_analyses.count(),
    }


def compute_financiers_consolides_kpis(date_debut=None, date_fin=None):
    """Calcule le chiffre d'affaires et les depenses consolides toutes
    directions confondues (labo, DAE, DMCT, DFIR, DAAF)."""
    from aero_finance.models import FactureDAE
    from daaf_finance.models import Depense, Recette
    from dfir_finance.models import FactureDFIR
    from dmct_finance.models import FactureDMCT

    ca_par_direction = {}

    factures_labo = Facture.objects.filter(statut="PAYEE")
    factures_dae = FactureDAE.objects.filter(statut="PAYEE")
    factures_dmct = FactureDMCT.objects.filter(statut="PAYEE")
    factures_dfir = FactureDFIR.objects.filter(statut="PAYEE")
    recettes_daaf = Recette.objects.filter(statut="ENCAISSEE")

    if date_debut and date_fin:
        factures_labo = factures_labo.filter(date_emission__range=(date_debut, date_fin))
        factures_dae = factures_dae.filter(date_emission__range=(date_debut, date_fin))
        factures_dmct = factures_dmct.filter(date_emission__range=(date_debut, date_fin))
        factures_dfir = factures_dfir.filter(date_emission__range=(date_debut, date_fin))
        recettes_daaf = recettes_daaf.filter(date_encaissement__range=(date_debut, date_fin))

    ca_par_direction["Laboratoire"] = float(factures_labo.aggregate(t=Sum("montant_ttc"))["t"] or 0)
    ca_par_direction["Aéronautique (DAE)"] = float(factures_dae.aggregate(t=Sum("montant_ttc"))["t"] or 0)
    ca_par_direction["Métrologie (DMCT)"] = float(factures_dmct.aggregate(t=Sum("montant_ttc"))["t"] or 0)
    ca_par_direction["Formation/Innovation/Recherche (DFIR)"] = float(
        factures_dfir.aggregate(t=Sum("montant_ttc"))["t"] or 0
    )
    ca_par_direction["DAAF (recettes)"] = float(recettes_daaf.aggregate(t=Sum("montant"))["t"] or 0)

    ca_consolide = sum(ca_par_direction.values())

    depenses_daaf = Depense.objects.filter(statut="PAYEE")
    factures_fournisseurs = FactureFournisseur.objects.filter(statut="PAYEE")
    if date_debut and date_fin:
        depenses_daaf = depenses_daaf.filter(date_paiement__range=(date_debut, date_fin))
        factures_fournisseurs = factures_fournisseurs.filter(date_reception__range=(date_debut, date_fin))

    depenses_consolidees = float(depenses_daaf.aggregate(t=Sum("montant"))["t"] or 0) + float(
        factures_fournisseurs.aggregate(t=Sum("montant_ttc"))["t"] or 0
    )

    return {
        "chiffre_affaires_consolide": ca_consolide,
        "chiffre_affaires_par_direction": ca_par_direction,
        "depenses_consolidees": depenses_consolidees,
        "resultat_net_estime": ca_consolide - depenses_consolidees,
    }


def compute_strategique_comptabilite_kpis(fournisseurs, tresorerie, pieces, facturation_kpis):
    """Calcule les KPI strategiques de la comptabilite, a partir des dicts
    deja calcules par les autres fonctions compute_*_kpis (pas de recalcul)."""
    composantes = [
        (tresorerie.get("taux_rapprochement"), 0.3),
        (pieces.get("taux_validation"), 0.25),
        (facturation_kpis.get("taux_recouvrement"), 0.25),
        (fournisseurs.get("taux_respect_echeances"), 0.2),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    indice_global = (
        round(sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids, 1)
        if total_poids else None
    )

    from django.db.models import Q

    six_mois = timezone.now().date() - timedelta(days=180)
    evolution_mensuelle = list(
        MouvementBancaire.objects.filter(date_mouvement__gte=six_mois)
        .annotate(mois=TruncMonth("date_mouvement"))
        .values("mois")
        .annotate(
            entrees=Sum("montant", filter=Q(type_mouvement="CREDIT")),
            sorties=Sum("montant", filter=Q(type_mouvement="DEBIT")),
        )
        .order_by("mois")
    )

    depenses_mensuelles_moyennes = None
    try:
        from daaf_finance.models import Depense

        depenses_recentes = Depense.objects.filter(statut="PAYEE", date_paiement__gte=six_mois)
        total_depenses = float(depenses_recentes.aggregate(t=Sum("montant"))["t"] or 0)
        depenses_mensuelles_moyennes = round(total_depenses / 6, 2)
    except Exception:
        depenses_mensuelles_moyennes = None

    taux_couverture_tresorerie = (
        round(tresorerie.get("solde_global", 0) / depenses_mensuelles_moyennes * 100, 1)
        if depenses_mensuelles_moyennes else None
    )

    return {
        "indice_global_performance_comptabilite": indice_global,
        "evolution_mensuelle_flux_bancaires": evolution_mensuelle,
        "taux_couverture_tresorerie": taux_couverture_tresorerie,
    }


class DashboardComptabiliteView(APIView):
    """Tableau de bord decisionnel Comptabilite : agrege fournisseurs,
    tresorerie, caisse, pieces comptables, ecritures, facturation/devis et
    financiers consolides toutes directions, + performance strategique."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        fournisseurs = compute_fournisseurs_kpis(date_debut, date_fin)
        tresorerie = compute_tresorerie_kpis(date_debut, date_fin)
        caisse = compute_caisse_kpis(date_debut, date_fin)
        pieces = compute_pieces_kpis(date_debut, date_fin)
        ecritures = compute_ecritures_kpis(date_debut, date_fin)
        facturation_kpis = compute_facturation_kpis(date_debut, date_fin)
        financiers_consolides = compute_financiers_consolides_kpis(date_debut, date_fin)
        strategique = compute_strategique_comptabilite_kpis(fournisseurs, tresorerie, pieces, facturation_kpis)

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "fournisseurs": fournisseurs,
            "tresorerie": tresorerie,
            "caisse": caisse,
            "pieces": pieces,
            "ecritures": ecritures,
            "facturation": facturation_kpis,
            "financiers_consolides": financiers_consolides,
            "strategique": strategique,
        })


class DashboardAgentComptableTresorView(APIView):
    """Vue transverse dediee a l'Agent Comptable du Tresor : supervision de
    l'ensemble des flux financiers de l'etablissement, toutes directions
    confondues."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from aero_finance.models import FactureDAE
        from dfir_finance.models import FactureDFIR
        from dmct_finance.models import FactureDMCT

        tresorerie = compute_tresorerie_kpis()
        caisse = compute_caisse_kpis()
        fournisseurs = compute_fournisseurs_kpis()
        pieces = compute_pieces_kpis()
        facturation_kpis = compute_facturation_kpis()
        strategique = compute_strategique_comptabilite_kpis(fournisseurs, tresorerie, pieces, facturation_kpis)

        factures_en_attente_validation = {
            "Laboratoire": Facture.objects.filter(statut="EN_ATTENTE_VALIDATION").count(),
            "Aéronautique (DAE)": FactureDAE.objects.filter(statut="EMISE").count(),
            "Métrologie (DMCT)": FactureDMCT.objects.filter(statut="EMISE").count(),
            "Formation/Innovation/Recherche (DFIR)": FactureDFIR.objects.filter(statut="EMISE").count(),
        }

        montant_du_fournisseurs = FactureFournisseur.objects.exclude(statut="PAYEE").aggregate(
            t=Sum("montant_ttc")
        )["t"] or 0

        rapprochements_en_attente = 0
        try:
            from comptabilite_tresorerie.models import RapprochementBancaire

            rapprochements_en_attente = RapprochementBancaire.objects.filter(valide=False).count()
        except Exception:
            rapprochements_en_attente = 0

        return Response({
            "generated_at": timezone.now().isoformat(),
            "solde_tresorerie_global": tresorerie.get("solde_global"),
            "solde_caisse_global": caisse.get("solde_total_caisses"),
            "factures_clients_en_attente_validation": factures_en_attente_validation,
            "montant_du_aux_fournisseurs": float(montant_du_fournisseurs),
            "pieces_comptables_en_attente": pieces.get("nombre_en_attente"),
            "rapprochements_en_attente": rapprochements_en_attente,
            "indice_global_performance": strategique.get("indice_global_performance_comptabilite"),
        })
