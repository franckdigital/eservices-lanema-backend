from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import FormateurDFIR
from .serializers import FormateurDFIRSerializer

# Répertoire des formateurs (gestion RH) : encadrement DFIR et plus — pas le
# palier "terrain" (leur page est Formations/Sessions).
DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_formateurs_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Formateurs (categorie 3) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    from dfir_formations.models import SessionFormation

    sessions = SessionFormation.objects.select_related("formation", "formateur__user").filter(formateur__isnull=False)
    if date_debut and date_fin:
        sessions = sessions.filter(date_debut__date__range=(date_debut, date_fin))

    termines = sessions.filter(statut="TERMINEE")
    heures_dispensees = sum(float(s.formation.duree_heures) for s in termines)

    formateurs_ids = list(sessions.values_list("formateur", flat=True).distinct())
    par_formateur = []
    for formateur_id in formateurs_ids:
        sessions_formateur = sessions.filter(formateur_id=formateur_id)
        formateur = FormateurDFIR.objects.filter(id=formateur_id).select_related("user").first()
        par_formateur.append({
            "formateur": (formateur.user.get_full_name() or formateur.user.username) if formateur else str(formateur_id),
            "formations_animees": sessions_formateur.filter(statut="TERMINEE").count(),
            "sessions_en_cours": sessions_formateur.filter(statut="EN_COURS").count(),
        })

    total_formateurs = FormateurDFIR.objects.count()
    taux_occupation = (
        round(sessions.filter(statut="EN_COURS").count() / total_formateurs * 100, 1) if total_formateurs else None
    )

    evaluation_moyenne = termines.filter(evaluation_formateur__isnull=False).aggregate(
        m=Avg("evaluation_formateur")
    )["m"]
    evaluation_moyenne = round(float(evaluation_moyenne), 2) if evaluation_moyenne is not None else None

    taux_disponibilite = (
        round(FormateurDFIR.objects.filter(disponible=True).count() / total_formateurs * 100, 1)
        if total_formateurs else None
    )

    nouveaux_formateurs = FormateurDFIR.objects.all()
    if date_debut and date_fin:
        nouveaux_formateurs = nouveaux_formateurs.filter(date_qualification__range=(date_debut, date_fin))

    return {
        "nombre_heures_formation_dispensees": heures_dispensees,
        "par_formateur": par_formateur,
        "taux_occupation_formateurs": taux_occupation,
        "evaluation_moyenne_formateurs": evaluation_moyenne,
        "taux_disponibilite_formateurs": taux_disponibilite,
        "nombre_nouveaux_formateurs_qualifies": nouveaux_formateurs.count(),
    }


class FormateurDFIRViewSet(viewsets.ModelViewSet):
    queryset = FormateurDFIR.objects.select_related("user").all()
    serializer_class = FormateurDFIRSerializer
    permission_classes = [DFIR_ENCADREMENT]


class FormateursKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_formateurs_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
