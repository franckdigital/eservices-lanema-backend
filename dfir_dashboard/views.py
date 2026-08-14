from datetime import timedelta

from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from dfir_assistance.models import MissionAssistance
from dfir_assistance.views import compute_assistance_kpis
from dfir_finance.views import compute_financiers_kpis
from dfir_formateurs.models import FormateurDFIR
from dfir_formateurs.views import compute_formateurs_kpis
from dfir_formations.models import Formation, InscriptionParticipant, SessionFormation, SupportPedagogique
from dfir_formations.views import compute_formations_kpis, compute_participants_kpis, compute_ressources_pedagogiques_kpis
from dfir_innovation.models import ProjetInnovation
from dfir_innovation.views import compute_innovation_kpis
from dfir_qualite.views import compute_qualite_kpis
from dfir_recherche.models import CollaborationRecherche, ProjetRecherche, PublicationScientifique
from dfir_recherche.views import compute_recherche_kpis


def compute_strategique_kpis(formations, participants, innovation, recherche, assistance, date_debut=None, date_fin=None):
    """Calcule les 13 KPI strategiques (categorie 10) de la DFIR, a partir
    des dicts deja calcules par les autres fonctions compute_*_kpis (pas de
    recalcul)."""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    debut_mois_precedent = (debut_mois - timedelta(days=1)).replace(day=1)

    sessions_mois_courant = SessionFormation.objects.filter(date_debut__date__gte=debut_mois).count()
    sessions_mois_precedent = SessionFormation.objects.filter(
        date_debut__date__gte=debut_mois_precedent, date_debut__date__lt=debut_mois
    ).count()
    taux_croissance_formation = (
        round((sessions_mois_courant - sessions_mois_precedent) / sessions_mois_precedent * 100, 1)
        if sessions_mois_precedent else None
    )

    projets_mois_courant = ProjetRecherche.objects.filter(date_debut__date__gte=debut_mois).count()
    projets_mois_precedent = ProjetRecherche.objects.filter(
        date_debut__date__gte=debut_mois_precedent, date_debut__date__lt=debut_mois
    ).count()
    taux_croissance_recherche = (
        round((projets_mois_courant - projets_mois_precedent) / projets_mois_precedent * 100, 1)
        if projets_mois_precedent else None
    )

    nombre_partenariats_strategiques = (
        CollaborationRecherche.objects.count() + ProjetInnovation.objects.filter(partenariat=True).count()
    )

    composantes = [
        (formations.get("taux_realisation_plan_annuel"), 0.25),
        (participants.get("taux_satisfaction_apprenants"), 0.25),
        (innovation.get("taux_reussite_projets"), 0.2),
        (recherche.get("taux_realisation_projets_recherche"), 0.15),
        (assistance.get("taux_satisfaction_entreprises"), 0.15),
    ]
    total_poids = sum(poids for valeur, poids in composantes if valeur is not None)
    indice_global = (
        round(sum(valeur * poids for valeur, poids in composantes if valeur is not None) / total_poids, 1)
        if total_poids else None
    )

    six_mois = today - timedelta(days=180)
    evolution_activites = list(
        SessionFormation.objects.filter(date_debut__date__gte=six_mois)
        .annotate(mois=TruncMonth("date_debut"))
        .values("mois")
        .annotate(nombre_sessions=Count("id"))
        .order_by("mois")
    )

    un_an = today - timedelta(days=365)
    deux_ans = today - timedelta(days=730)
    entreprises_annee_courante = set(
        SessionFormation.objects.filter(date_debut__date__gte=un_an, entreprise__isnull=False)
        .values_list("entreprise_id", flat=True)
    )
    entreprises_annee_precedente = set(
        SessionFormation.objects.filter(date_debut__date__gte=deux_ans, date_debut__date__lt=un_an, entreprise__isnull=False)
        .values_list("entreprise_id", flat=True)
    )
    entreprises_renouvelees = entreprises_annee_courante & entreprises_annee_precedente
    taux_renouvellement = (
        round(len(entreprises_renouvelees) / len(entreprises_annee_precedente) * 100, 1)
        if entreprises_annee_precedente else None
    )

    return {
        "nombre_total_personnes_formees": participants.get("nombre_total_participants"),
        "nombre_total_entreprises_accompagnees": assistance.get("nombre_entreprises_accompagnees"),
        "taux_insertion_application_competences": None,
        "taux_insertion_application_competences_note": (
            "Non mesurable : aucun suivi post-formation des competences appliquees n'est trace dans le systeme."
        ),
        "nombre_certifications_delivrees": participants.get("nombre_participants_certifies"),
        "taux_croissance_activites_formation": taux_croissance_formation,
        "taux_croissance_activites_recherche": taux_croissance_recherche,
        "nombre_partenariats_strategiques": nombre_partenariats_strategiques,
        "impact_formations_sur_performances_entreprises": None,
        "impact_formations_sur_performances_entreprises_note": (
            "Non mesurable : aucune donnee de performance des entreprises accompagnees n'est collectee."
        ),
        "indice_global_performance_dfir": indice_global,
        "contribution_objectifs_strategiques_lanema": None,
        "contribution_objectifs_strategiques_lanema_note": (
            "Non mesurable : indicateur qualitatif sans source de donnees dediee."
        ),
        "evolution_mensuelle_activites": evolution_activites,
        "taux_renouvellement_clients": taux_renouvellement,
        "taux_atteinte_objectifs_annuels": formations.get("taux_realisation_plan_annuel"),
    }


class DashboardDFIRView(APIView):
    """Tableau de bord decisionnel DFIR : agrege les 9 categories de KPI de
    la Direction Formation, Innovation et Recherche (formations, participants,
    formateurs, innovation, recherche, assistance technique, qualite,
    financiers, ressources pedagogiques) + performance strategique."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        formations = compute_formations_kpis(date_debut, date_fin)
        participants = compute_participants_kpis(date_debut, date_fin)
        ressources_pedagogiques = compute_ressources_pedagogiques_kpis(date_debut, date_fin)
        formateurs = compute_formateurs_kpis(date_debut, date_fin)
        innovation = compute_innovation_kpis(date_debut, date_fin)
        recherche = compute_recherche_kpis(date_debut, date_fin)
        assistance = compute_assistance_kpis(date_debut, date_fin)
        qualite = compute_qualite_kpis(date_debut, date_fin)
        financiers = compute_financiers_kpis(date_debut, date_fin)
        strategique = compute_strategique_kpis(formations, participants, innovation, recherche, assistance, date_debut, date_fin)

        return Response({
            "generated_at": timezone.now().isoformat(),
            "periode": {"debut": date_debut, "fin": date_fin},
            "formations": formations,
            "participants": participants,
            "ressources_pedagogiques": ressources_pedagogiques,
            "formateurs": formateurs,
            "innovation": innovation,
            "recherche": recherche,
            "assistance": assistance,
            "qualite": qualite,
            "financiers": financiers,
            "strategique": strategique,
        })


class DashboardDFIRDirecteurView(APIView):
    """Vue condensee Directeur de la DFIR (9 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        formations = compute_formations_kpis()
        participants = compute_participants_kpis()
        innovation = compute_innovation_kpis()
        recherche = compute_recherche_kpis()
        assistance = compute_assistance_kpis()
        financiers = compute_financiers_kpis()
        strategique = compute_strategique_kpis(formations, participants, innovation, recherche, assistance)

        sessions = SessionFormation.objects.all()

        return Response({
            "sessions_planifiees": sessions.filter(statut="PLANIFIEE").count(),
            "sessions_en_cours": sessions.filter(statut="EN_COURS").count(),
            "sessions_realisees": sessions.filter(statut="TERMINEE").count(),
            "nombre_participants_et_entreprises": {
                "participants": participants["nombre_total_participants"],
                "entreprises": participants["nombre_entreprises_formees"],
            },
            "taux_satisfaction": participants["taux_satisfaction_apprenants"],
            "chiffre_affaires_par_activite": {
                "formations": financiers["chiffre_affaires_formations"],
                "assistance": financiers["chiffre_affaires_assistance"],
                "recherche": financiers["chiffre_affaires_recherche"],
            },
            "projets_recherche_en_cours": ProjetRecherche.objects.filter(statut="EN_COURS").count(),
            "projets_innovation_en_cours": ProjetInnovation.objects.filter(statut="EN_COURS").count(),
            "missions_assistance_en_cours": MissionAssistance.objects.filter(statut="EN_COURS").count(),
            "taux_realisation_plan_annuel": formations["taux_realisation_plan_annuel"],
            "indice_global_performance": strategique["indice_global_performance_dfir"],
        })


class DashboardDFIRChefServiceFormationView(APIView):
    """Vue condensee Chef de service Formation (5 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        sessions_a_venir = SessionFormation.objects.filter(
            statut="PLANIFIEE", date_debut__date__gte=today
        ).order_by("date_debut")

        sessions_avec_inscriptions = SessionFormation.objects.annotate(nb_inscrits=Count("inscriptions"))
        sessions_avec_capacite = sessions_avec_inscriptions.filter(capacite_max__gt=0)
        taux_remplissage = None
        if sessions_avec_capacite.exists():
            taux_moyens = [
                s.nb_inscrits / s.capacite_max * 100 for s in sessions_avec_capacite
            ]
            taux_remplissage = round(sum(taux_moyens) / len(taux_moyens), 1)

        inscriptions_evaluees = InscriptionParticipant.objects.filter(reussite__isnull=False)
        taux_reussite = (
            round(inscriptions_evaluees.filter(reussite=True).count() / inscriptions_evaluees.count() * 100, 1)
            if inscriptions_evaluees.count() else None
        )

        evaluation_formateurs = list(
            SessionFormation.objects.filter(evaluation_formateur__isnull=False, formateur__isnull=False)
            .values("formateur__user__username")
            .annotate(note_moyenne=Avg("evaluation_formateur"))
            .order_by("-note_moyenne")[:10]
        )

        return Response({
            "calendrier_sessions_a_venir": list(
                sessions_a_venir[:10].values("id", "formation__titre", "date_debut", "capacite_max")
            ),
            "taux_remplissage_formations": taux_remplissage,
            "taux_reussite_participants": taux_reussite,
            "evaluation_formateurs": evaluation_formateurs,
            "formations_a_venir": sessions_a_venir.count(),
        })


class DashboardDFIRChefServiceRechercheInnovationView(APIView):
    """Vue condensee Chef de service Recherche et Innovation (5 widgets)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projets_recherche_actifs = ProjetRecherche.objects.filter(statut="EN_COURS")

        etat_avancement = list(
            ProjetRecherche.objects.values("statut").annotate(nombre=Count("id")).order_by("statut")
        )

        publications_realisees = PublicationScientifique.objects.count()
        innovations_developpees = ProjetInnovation.objects.filter(mis_en_oeuvre=True).count()

        partenariats_scientifiques = list(
            CollaborationRecherche.objects.order_by("-date_debut")[:10].values(
                "nom_partenaire", "type_partenaire", "date_debut"
            )
        )

        return Response({
            "projets_recherche_actifs": projets_recherche_actifs.count(),
            "etat_avancement_projets": etat_avancement,
            "publications_realisees": publications_realisees,
            "innovations_developpees": innovations_developpees,
            "partenariats_scientifiques": partenariats_scientifiques,
        })


class DashboardDFIRFormateurView(APIView):
    """Vue condensee Formateur, scopee sur request.user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        formateur = FormateurDFIR.objects.filter(user=request.user).first()
        if not formateur:
            return Response({
                "sessions_assignees": 0,
                "nombre_stagiaires": 0,
                "evaluation_moyenne_apprenants": None,
                "heures_dispensees": 0,
                "supports_a_mettre_a_jour": 0,
                "_note": "Aucun profil formateur associe a cet utilisateur.",
            })

        sessions = SessionFormation.objects.filter(formateur=formateur)
        inscriptions = InscriptionParticipant.objects.filter(session__in=sessions)

        heures_dispensees = sum(
            float(s.formation.duree_heures) for s in sessions.filter(statut="TERMINEE").select_related("formation")
        )

        evalues_reussite = inscriptions.filter(reussite__isnull=False)
        evaluation_moyenne = (
            round(evalues_reussite.filter(reussite=True).count() / evalues_reussite.count() * 100, 1)
            if evalues_reussite.count() else None
        )

        formations_formateur = Formation.objects.filter(sessions__formateur=formateur).distinct()
        supports_a_maj = SupportPedagogique.objects.filter(
            formation__in=formations_formateur, date_derniere_maj__isnull=True
        ).count()

        return Response({
            "sessions_assignees": sessions.count(),
            "nombre_stagiaires": inscriptions.values("participant").distinct().count(),
            "evaluation_moyenne_apprenants": evaluation_moyenne,
            "heures_dispensees": heures_dispensees,
            "supports_a_mettre_a_jour": supports_a_maj,
        })
