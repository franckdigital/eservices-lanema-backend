from datetime import timedelta

from django.db.models import Count, F
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from clients.views import compute_clients_kpis
from facturation.views import compute_financiers_kpis
from metrologie.views import compute_equipements_kpis
from qualite.models import ActionQualite, Audit, Essai, NonConformite
from qualite.views import (
    compute_echantillons_kpis,
    compute_essais_kpis,
    compute_qualite_iso_kpis,
    compute_techniciens_kpis,
)
from reporting.models import RapportEssai
from reporting.views import compute_rapports_essais_kpis
from stock.modules.reactifs_kpi import compute_reactifs_kpis


def _business_days(date_debut, date_fin):
    jours = 0
    current = date_debut
    while current <= date_fin:
        if current.weekday() < 5:
            jours += 1
        current += timedelta(days=1)
    return jours


def compute_performance_globale_kpis(echantillons, essais, equipements, techniciens, qualite_iso, clients=None, date_debut=None, date_fin=None):
    """Calcule les 10 KPI de performance globale (#81-90), a partir des dicts
    deja calcules par les autres fonctions compute_*_kpis (pas de recalcul)."""
    today = timezone.now().date()
    if date_debut and date_fin:
        periode_debut, periode_fin = date_debut, date_fin
        if isinstance(periode_debut, str):
            periode_debut = timezone.datetime.strptime(periode_debut, "%Y-%m-%d").date()
        if isinstance(periode_fin, str):
            periode_fin = timezone.datetime.strptime(periode_fin, "%Y-%m-%d").date()
    else:
        periode_debut, periode_fin = today.replace(day=1), today

    jours_ouvres = _business_days(periode_debut, periode_fin) or 1
    nb_analyses = essais["nombre_total_essais_realises"]
    analyses_par_jour = round(nb_analyses / jours_ouvres, 2)

    from laboratoires.models import Laboratoire

    capacite_totale = sum(l.capacite_journaliere for l in Laboratoire.objects.all())
    capacite_utilisation = (
        round(nb_analyses / (capacite_totale * jours_ouvres) * 100, 1) if capacite_totale else None
    )

    composantes = [
        (echantillons.get("taux_conformite_echantillons"), 0.25),
        (essais.get("respect_delais_analyse"), 0.2),
        (equipements.get("taux_disponibilite_equipements"), 0.2),
        (techniciens.get("taux_qualite_global"), 0.2),
        (qualite_iso.get("taux_conformite_procedures"), 0.15),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    indice_global = (
        round(sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids, 1)
        if total_poids else None
    )

    return {
        "nombre_total_analyses_realisees": nb_analyses,
        "delai_moyen_traitement_dossier_jours": (clients or {}).get("delai_moyen_traitement_demande_jours"),
        "taux_global_conformite": echantillons.get("taux_conformite_echantillons"),
        "taux_respect_delais": essais.get("respect_delais_analyse"),
        "taux_disponibilite_equipements": equipements.get("taux_disponibilite_equipements"),
        "productivite_globale": essais.get("productivite_laboratoires"),
        "qualite_globale_resultats": techniciens.get("taux_qualite_global"),
        "capacite_utilisation_laboratoire": capacite_utilisation,
        "nombre_analyses_par_jour": analyses_par_jour,
        "indice_global_performance_laboratoire": indice_global,
    }


class DashboardDEAView(APIView):
    """Tableau de bord decisionnel DEA : agrege les 10 categories de KPI du
    module laboratoire (echantillons, essais, rapports, techniciens,
    equipements, reactifs, qualite ISO, clients, financiers) + performance
    globale."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        echantillons = compute_echantillons_kpis(date_debut, date_fin)
        essais = compute_essais_kpis(date_debut, date_fin)
        rapports = compute_rapports_essais_kpis(date_debut, date_fin)
        techniciens = compute_techniciens_kpis(date_debut, date_fin)
        equipements = compute_equipements_kpis(date_debut, date_fin)
        reactifs = compute_reactifs_kpis(date_debut, date_fin)
        qualite_iso = compute_qualite_iso_kpis(date_debut, date_fin)
        clients = compute_clients_kpis(date_debut, date_fin)
        financiers = compute_financiers_kpis(date_debut, date_fin)
        performance_globale = compute_performance_globale_kpis(
            echantillons, essais, equipements, techniciens, qualite_iso, clients, date_debut, date_fin
        )

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "echantillons": echantillons,
            "essais": essais,
            "rapports_essais": rapports,
            "techniciens": techniciens,
            "equipements": equipements,
            "reactifs": reactifs,
            "qualite_iso": qualite_iso,
            "clients": clients,
            "financiers": financiers,
            "performance_globale": performance_globale,
        })


class DashboardDEADGView(APIView):
    """Vue condensee Direction Generale (9 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        echantillons = compute_echantillons_kpis()
        essais = compute_essais_kpis()
        equipements = compute_equipements_kpis()
        techniciens = compute_techniciens_kpis()
        qualite_iso = compute_qualite_iso_kpis()
        clients = compute_clients_kpis()
        financiers = compute_financiers_kpis()
        performance_globale = compute_performance_globale_kpis(
            echantillons, essais, equipements, techniciens, qualite_iso, clients
        )

        analyses_en_retard = Essai.objects.filter(
            date_fin_prevue__lt=today
        ).exclude(statut__in=["TERMINE", "VALIDE", "ANNULE"]).count()

        return Response({
            "nombre_total_echantillons_recus": echantillons["nombre_echantillons_recus"],
            "dossiers_en_attente": echantillons["nombre_echantillons_en_attente"],
            "taux_conformite_produits": echantillons["taux_conformite_echantillons"],
            "chiffre_affaires_par_laboratoire": financiers["recettes_par_laboratoire"],
            "productivite_globale": essais["productivite_laboratoires"],
            "disponibilite_equipements": equipements["taux_disponibilite_equipements"],
            "analyses_en_retard": analyses_en_retard,
            "reclamations_clients": clients["nombre_reclamations"],
            "indice_global_performance": performance_globale["indice_global_performance_laboratoire"],
        })


class DashboardDEALaboView(APIView):
    """Vue condensee Responsable de laboratoire (8 widgets), optionnellement
    filtree par ?laboratoire_id=."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        laboratoire_id = request.query_params.get("laboratoire_id")

        from metrologie.models import Equipement

        essais_lab = Essai.objects.all()
        equipements_lab = Equipement.objects.all()
        rapports_lab = RapportEssai.objects.all()
        if laboratoire_id:
            essais_lab = essais_lab.filter(laboratoire_id=laboratoire_id)
            equipements_lab = equipements_lab.filter(laboratoire_id=laboratoire_id)
            rapports_lab = rapports_lab.filter(essai__laboratoire_id=laboratoire_id)

        from qualite.models import Echantillon

        echantillons_aujourdhui = Echantillon.objects.filter(date_reception=today)
        if laboratoire_id:
            echantillons_aujourdhui = echantillons_aujourdhui.filter(
                essais__laboratoire_id=laboratoire_id
            ).distinct()

        charge_par_technicien = list(
            essais_lab.filter(statut="EN_COURS")
            .exclude(technicien_user__isnull=True)
            .values("technicien_user__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        reactifs = compute_reactifs_kpis()
        essais_avec_dates = essais_lab.filter(date_fin__isnull=False, date_fin_prevue__isnull=False)
        nb_dans_delais = essais_avec_dates.filter(date_fin__lte=F("date_fin_prevue")).count()
        respect_delais = (
            round(nb_dans_delais / essais_avec_dates.count() * 100, 1) if essais_avec_dates.count() else None
        )

        return Response({
            "echantillons_recus_aujourdhui": echantillons_aujourdhui.count(),
            "analyses_en_cours": essais_lab.filter(statut="EN_COURS").count(),
            "charge_travail_techniciens": charge_par_technicien,
            "equipements_indisponibles": equipements_lab.filter(
                statut__in=["HORS_SERVICE", "MAINTENANCE"]
            ).count(),
            "etalonnages_a_realiser": equipements_lab.filter(
                date_prochain_etalonnage__lte=today + timedelta(days=30)
            ).count(),
            "stock_reactifs": reactifs,
            "rapports_a_valider": rapports_lab.filter(statut="EN_ATTENTE_VALIDATION").count(),
            "respect_delais": respect_delais,
        })


class DashboardDEATechnicienView(APIView):
    """Vue condensee Technicien/Analyste, scopee sur request.user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        essais_user = Essai.objects.filter(technicien_user=request.user)
        essais_termines = essais_user.filter(statut__in=["TERMINE", "VALIDE"])

        duree_qs = essais_user.filter(date_debut__isnull=False, date_fin__isnull=False)
        temps_moyen = None
        if duree_qs.exists():
            durees = [(e.date_fin - e.date_debut).days for e in duree_qs]
            temps_moyen = round(sum(durees) / len(durees), 1)

        total_user = essais_user.count()
        nb_erreurs = essais_user.filter(erreur_detectee=True).count()
        taux_conformite = round((1 - nb_erreurs / total_user) * 100, 1) if total_user else None

        return Response({
            "analyses_assignees": total_user,
            "analyses_terminees": essais_termines.count(),
            "temps_moyen_par_analyse_jours": temps_moyen,
            "rapports_a_rediger": RapportEssai.objects.filter(
                essai__technicien_user=request.user, statut="BROUILLON"
            ).count(),
            "planning_utilisation_equipements": None,
            "planning_utilisation_equipements_note": (
                "Non mesurable : aucun lien direct entre un essai et l'equipement utilise n'est trace."
            ),
            "taux_conformite_essais": taux_conformite,
        })


class DashboardDEAQualiteResponsableView(APIView):
    """Vue condensee Responsable Qualite (7 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        non_conformites = NonConformite.objects.all()
        nb_total_nc = non_conformites.count()
        nb_nc_avec_action_cloturee = non_conformites.filter(actions__statut="CLOTUREE").distinct().count()
        nb_nc_ouvertes = nb_total_nc - nb_nc_avec_action_cloturee

        from metrologie.models import Equipement

        etalonnages_a_echeance = Equipement.objects.filter(
            date_prochain_etalonnage__lte=today + timedelta(days=30)
        ).count()

        audits_planifies = Audit.objects.filter(date_audit__gte=today).count()

        qualite_iso = compute_qualite_iso_kpis()

        historique_ecarts = list(
            non_conformites.order_by("-date_creation")[:10].values(
                "numero", "type_nc", "gravite", "description", "date_creation"
            )
        )

        return Response({
            "non_conformites_ouvertes": nb_nc_ouvertes,
            "actions_correctives_en_cours": ActionQualite.objects.filter(
                type="CORRECTIVE", statut="EN_COURS"
            ).count(),
            "audits_planifies": audits_planifies,
            "etalonnages_a_echeance": etalonnages_a_echeance,
            "indicateurs_iso_17025": qualite_iso,
            "historique_ecarts": historique_ecarts,
        })
