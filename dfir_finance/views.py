from django.db.models import Avg, Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from dfir_formations.models import Formation, SessionFormation
from core.direction_access import direction_permission

from .models import FactureDFIR
from .serializers import FactureDFIRSerializer

# Les factures sont réservées au palier "direction" (Admin/Directeur). L'agrégat
# KPI reste ouvert à tout membre DFIR, comme les autres endpoints KPI, pour ne
# pas casser le tableau de bord DFIR existant.
DFIR_DIRECTION = direction_permission('DFIR', feature_key='dfir_view_finance')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_financiers_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Financiers (categorie 8) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    factures = FactureDFIR.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_emission__range=(date_debut, date_fin))

    factures_payees = factures.filter(statut="PAYEE")
    ca_formations = float(
        factures_payees.filter(type_prestation="FORMATION").aggregate(t=Sum("montant_ttc"))["t"] or 0
    )
    ca_assistance = float(
        factures_payees.filter(type_prestation="ASSISTANCE").aggregate(t=Sum("montant_ttc"))["t"] or 0
    )
    ca_recherche = float(
        factures_payees.filter(type_prestation="RECHERCHE").aggregate(t=Sum("montant_ttc"))["t"] or 0
    )

    sessions = SessionFormation.objects.all()
    if date_debut and date_fin:
        sessions = sessions.filter(date_debut__date__range=(date_debut, date_fin))
    cout_moyen_formation = sessions.filter(cout_revient__isnull=False).aggregate(m=Avg("cout_revient"))["m"]
    cout_moyen_formation = round(float(cout_moyen_formation), 2) if cout_moyen_formation is not None else None

    rentabilite_par_programme = []
    for formation in Formation.objects.all():
        sessions_formation = sessions.filter(formation=formation)
        ca_formation = float(
            factures_payees.filter(session__formation=formation).aggregate(t=Sum("montant_ttc"))["t"] or 0
        )
        cout_formation = float(
            sessions_formation.filter(cout_revient__isnull=False).aggregate(t=Sum("cout_revient"))["t"] or 0
        )
        if ca_formation or cout_formation:
            rentabilite_par_programme.append({
                "formation": formation.titre,
                "chiffre_affaires": ca_formation,
                "cout": cout_formation,
                "rentabilite": round(ca_formation - cout_formation, 2),
            })

    formateurs_ids = list(sessions.filter(formateur__isnull=False).values_list("formateur", flat=True).distinct())
    revenus_par_formateur = []
    for formateur_id in formateurs_ids:
        ca_formateur = float(
            factures_payees.filter(session__formateur_id=formateur_id).aggregate(t=Sum("montant_ttc"))["t"] or 0
        )
        formateur_session = sessions.filter(formateur_id=formateur_id).select_related("formateur__user").first()
        nom = (
            formateur_session.formateur.user.get_full_name() or formateur_session.formateur.user.username
        ) if formateur_session and formateur_session.formateur else str(formateur_id)
        revenus_par_formateur.append({"formateur": nom, "chiffre_affaires": ca_formateur})

    total_factures = factures.count()
    taux_recouvrement = (
        round(factures_payees.count() / total_factures * 100, 1) if total_factures else None
    )

    return {
        "chiffre_affaires_formations": ca_formations,
        "chiffre_affaires_assistance": ca_assistance,
        "chiffre_affaires_recherche": ca_recherche,
        "cout_moyen_formation": cout_moyen_formation,
        "rentabilite_par_programme": rentabilite_par_programme,
        "taux_recouvrement": taux_recouvrement,
        "revenus_par_formateur": revenus_par_formateur,
    }


class FactureDFIRViewSet(viewsets.ModelViewSet):
    queryset = FactureDFIR.objects.select_related("entreprise", "session__formation", "mission", "projet_recherche").all()
    serializer_class = FactureDFIRSerializer
    permission_classes = [DFIR_DIRECTION]


class FinanciersKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_financiers_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
