from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from dmct_clients.views import compute_clients_kpis
from dmct_demandes.models import DemandeDMCT
from dmct_demandes.views import compute_demandes_kpis
from dmct_equipements_rh.models import EquipementReference
from dmct_equipements_rh.views import compute_equipements_reference_kpis, compute_rh_kpis
from dmct_finance.models import FactureDMCT
from dmct_finance.views import compute_financiers_kpis
from dmct_inspections.models import InspectionDMCT
from dmct_inspections.views import compute_inspections_kpis
from dmct_instruments.models import CertificatDMCT
from dmct_instruments.views import compute_instruments_kpis
from dmct_prestations.models import PrestationDMCT
from dmct_prestations.views import compute_prestations_kpis
from dmct_qualite.views import compute_qualite_kpis


def compute_strategique_kpis(instruments, demandes, prestations, qualite, equipements_reference, clients):
    """Calcule les 10 KPI strategiques (categorie 10) de la DMCT, a partir
    des dicts deja calcules par les autres fonctions compute_*_kpis (pas de
    recalcul)."""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    debut_mois_precedent = (debut_mois - timedelta(days=1)).replace(day=1)

    prestations_mois = PrestationDMCT.objects.filter(statut="TERMINEE", date_fin__date__gte=debut_mois)
    verifies_mois = prestations_mois.filter(type_prestation="VERIFICATION").count()
    etalonnes_mois = prestations_mois.filter(type_prestation="ETALONNAGE").count()

    six_mois = today - timedelta(days=180)
    evolution_activite = list(
        PrestationDMCT.objects.filter(date_fin__date__gte=six_mois, statut="TERMINEE")
        .annotate(mois=TruncMonth("date_fin"))
        .values("mois")
        .annotate(nombre_prestations=Count("id"))
        .order_by("mois")
    )

    prestations_mois_precedent = PrestationDMCT.objects.filter(
        statut="TERMINEE", date_fin__date__gte=debut_mois_precedent, date_fin__date__lt=debut_mois
    ).count()
    prestations_mois_courant = prestations_mois.count()
    taux_croissance = (
        round((prestations_mois_courant - prestations_mois_precedent) / prestations_mois_precedent * 100, 1)
        if prestations_mois_precedent else None
    )

    delai_traitement_dossiers = (
        round(prestations.get("temps_moyen_prestation_heures") / 24, 1)
        if prestations.get("temps_moyen_prestation_heures") is not None else None
    )

    composantes = [
        (instruments.get("taux_conformite_instruments"), 0.25),
        (prestations.get("taux_respect_delais_sla"), 0.25),
        (equipements_reference.get("taux_disponibilite_equipements"), 0.2),
        (qualite.get("taux_conformite_procedures"), 0.15),
        (clients.get("taux_satisfaction_clients"), 0.15),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    indice_global = (
        round(sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids, 1)
        if total_poids else None
    )

    secteurs_couverts = len(prestations.get("prestations_par_secteur") or {})
    taux_couverture_secteurs = round(secteurs_couverts / 4 * 100, 1)

    return {
        "nombre_instruments_verifies_mois_courant": verifies_mois,
        "nombre_instruments_etalonnes_mois_courant": etalonnes_mois,
        "evolution_mensuelle_activite": evolution_activite,
        "taux_global_conformite_instruments": instruments.get("taux_conformite_instruments"),
        "delai_moyen_traitement_dossiers_jours": delai_traitement_dossiers,
        "taux_disponibilite_equipements_metrologie": equipements_reference.get("taux_disponibilite_equipements"),
        "respect_engagements_sla": prestations.get("taux_respect_delais_sla"),
        "taux_croissance_prestations": taux_croissance,
        "indice_global_performance_dmct": indice_global,
        "taux_couverture_secteurs": taux_couverture_secteurs,
    }


class DashboardDMCTView(APIView):
    """Tableau de bord decisionnel DMCT : agrege les 9 categories de KPI de
    la Direction de la Metrologie et des Controles Techniques (demandes,
    instruments, prestations, qualite, equipements de reference, RH,
    inspections, financiers, clients) + performance strategique."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        demandes = compute_demandes_kpis(date_debut, date_fin)
        instruments = compute_instruments_kpis(date_debut, date_fin)
        prestations = compute_prestations_kpis(date_debut, date_fin)
        qualite = compute_qualite_kpis(date_debut, date_fin)
        equipements_reference = compute_equipements_reference_kpis(date_debut, date_fin)
        rh = compute_rh_kpis(date_debut, date_fin)
        inspections_data = compute_inspections_kpis(date_debut, date_fin)
        financiers = compute_financiers_kpis(date_debut, date_fin)
        clients = compute_clients_kpis(date_debut, date_fin)
        strategique = compute_strategique_kpis(instruments, demandes, prestations, qualite, equipements_reference, clients)

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "demandes": demandes,
            "instruments": instruments,
            "prestations": prestations,
            "qualite": qualite,
            "equipements_reference": equipements_reference,
            "rh": rh,
            "inspections": inspections_data,
            "financiers": financiers,
            "clients": clients,
            "strategique": strategique,
        })


class DashboardDMCTDirecteurView(APIView):
    """Vue condensee Directeur de la DMCT (9 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        demandes_recues = DemandeDMCT.objects.all()
        demandes_en_attente = demandes_recues.filter(statut="EN_ATTENTE")

        instruments = compute_instruments_kpis()
        prestations = compute_prestations_kpis()
        equipements_reference = compute_equipements_reference_kpis()
        qualite = compute_qualite_kpis()
        clients = compute_clients_kpis()
        strategique = compute_strategique_kpis(instruments, compute_demandes_kpis(), prestations, qualite, equipements_reference, clients)

        prestations_en_retard = PrestationDMCT.objects.filter(
            date_fin_prevue__lt=today
        ).exclude(statut__in=["TERMINEE", "ANNULEE"]).count()

        equipements_indisponibles = EquipementReference.objects.filter(statut="HORS_SERVICE").count()

        ca_mensuel = FactureDMCT.objects.filter(
            statut="PAYEE", date_emission__date__gte=today.replace(day=1)
        ).count()

        alertes_echeances = EquipementReference.objects.filter(
            date_prochain_etalonnage__lte=today + timedelta(days=30)
        ).count()

        return Response({
            "nombre_demandes_recues": demandes_recues.count(),
            "nombre_demandes_en_attente": demandes_en_attente.count(),
            "instruments_controles": instruments["nombre_instruments_controles"],
            "instruments_verifies": instruments["nombre_instruments_verifies"],
            "instruments_etalonnes": instruments["nombre_instruments_etalonnes"],
            "taux_conformite_instruments": instruments["taux_conformite_instruments"],
            "prestations_en_retard": prestations_en_retard,
            "equipements_indisponibles": equipements_indisponibles,
            "chiffre_affaires_mensuel": ca_mensuel,
            "reclamations_clients": clients["nombre_reclamations"],
            "alertes_echeances_etalonnage": alertes_echeances,
            "indice_global_performance": strategique["indice_global_performance_dmct"],
        })


class DashboardDMCTChefServiceView(APIView):
    """Vue condensee Chef de service (6 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prestations_en_cours = PrestationDMCT.objects.filter(statut="EN_COURS")

        charge_par_agent = list(
            prestations_en_cours.exclude(agent__isnull=True)
            .values("agent__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        controles_a_realiser = InspectionDMCT.objects.filter(
            categorie="CONTROLE_TECHNIQUE", date_cloture__isnull=True
        ).count()

        certifications_terminees = PrestationDMCT.objects.filter(
            type_prestation="CERTIFICATION", statut="TERMINEE", instrument__isnull=False
        ).select_related("instrument")
        instruments_ids_certifies = set(CertificatDMCT.objects.values_list("instrument_id", flat=True))
        certificats_a_valider = sum(
            1 for p in certifications_terminees if p.instrument_id not in instruments_ids_certifies
        )

        equipements_a_maintenir = EquipementReference.objects.filter(statut="MAINTENANCE").count()

        return Response({
            "interventions_planifiees": PrestationDMCT.objects.filter(statut="EN_COURS").count(),
            "charge_travail_metrologues": charge_par_agent,
            "prestations_en_cours": prestations_en_cours.count(),
            "controles_techniques_a_realiser": controles_a_realiser,
            "certificats_a_valider": certificats_a_valider,
            "equipements_a_maintenir": equipements_a_maintenir,
        })


class DashboardDMCTMetrologueView(APIView):
    """Vue condensee Metrologue/Inspecteur, scopee sur request.user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prestations_user = PrestationDMCT.objects.filter(agent=request.user)
        prestations_en_cours = prestations_user.filter(statut="EN_COURS")
        prestations_terminees = prestations_user.filter(statut="TERMINEE", date_debut__isnull=False, date_fin__isnull=False)

        durees = [(p.date_fin - p.date_debut).total_seconds() / 3600 for p in prestations_terminees]
        temps_moyen = round(sum(durees) / len(durees), 1) if durees else None

        instruments_ids_certifies = set(CertificatDMCT.objects.values_list("instrument_id", flat=True))
        certifications_a_produire = sum(
            1 for p in prestations_user.filter(type_prestation="CERTIFICATION", statut="TERMINEE", instrument__isnull=False)
            if p.instrument_id not in instruments_ids_certifies
        )

        total_user = prestations_user.count()
        score_performance = round(prestations_terminees.count() / total_user * 100, 1) if total_user else None

        historique = list(
            prestations_terminees.order_by("-date_fin")[:10].values(
                "reference", "type_prestation", "date_debut", "date_fin", "statut"
            )
        )

        return Response({
            "interventions_assignees": total_user,
            "interventions_en_cours": prestations_en_cours.count(),
            "instruments_a_controler": prestations_en_cours.filter(instrument__isnull=False).count(),
            "certificats_a_produire": certifications_a_produire,
            "temps_moyen_intervention_heures": temps_moyen,
            "historique_prestations": historique,
            "score_individuel_performance": score_performance,
        })
