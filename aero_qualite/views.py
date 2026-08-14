from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_maintenance.models import OrdreTravail
from core.direction_access import direction_permission

from .models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE
from .serializers import ActionCorrectiveDAESerializer, AuditQualiteDAESerializer, NonConformiteDAESerializer

DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')


def compute_qualite_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Qualite (categorie 4) de la DAE. Reutilisable
    directement par le tableau de bord DAE."""
    non_conformites = NonConformiteDAE.objects.all()
    if date_debut and date_fin:
        non_conformites = non_conformites.filter(date_creation__range=(date_debut, date_fin))

    actions = ActionCorrectiveDAE.objects.all()
    audits = AuditQualiteDAE.objects.all()
    if date_debut and date_fin:
        audits = audits.filter(date_audit__range=(date_debut, date_fin))

    total_nc = non_conformites.count()
    taux_cloture = (
        round(non_conformites.filter(statut="CLOTUREE").count() / total_nc * 100, 1) if total_nc else None
    )

    total_audits = audits.count()
    taux_conformite_procedures = (
        round(audits.filter(resultat="CONFORME").count() / total_audits * 100, 1) if total_audits else None
    )

    # Reprises apres maintenance : approximation documentee — un nouvel ordre de
    # travail est ouvert sur le meme aeronef apres une non-conformite liee a un
    # ordre de travail anterieur.
    nb_reprises = 0
    for nc in non_conformites.filter(ordre_travail__isnull=False).select_related("ordre_travail__aeronef"):
        aeronef = nc.ordre_travail.aeronef
        if OrdreTravail.objects.filter(aeronef=aeronef, date_demande__date__gt=nc.date_creation).exists():
            nb_reprises += 1

    ordres_termines = OrdreTravail.objects.filter(statut="TERMINE")
    if date_debut and date_fin:
        ordres_termines = ordres_termines.filter(date_demande__date__range=(date_debut, date_fin))
    total_termines = ordres_termines.count()
    ordres_sans_nc = ordres_termines.exclude(non_conformites__isnull=False).distinct().count()
    taux_reussite_premier_passage = (
        round(ordres_sans_nc / total_termines * 100, 1) if total_termines else None
    )

    return {
        "nombre_non_conformites": total_nc,
        "nombre_actions_correctives": actions.count(),
        "taux_cloture_non_conformites": taux_cloture,
        "nombre_audits": total_audits,
        "taux_conformite_procedures": taux_conformite_procedures,
        "nombre_reprises_apres_maintenance": nb_reprises,
        "taux_reussite_premier_passage": taux_reussite_premier_passage,
    }


class NonConformiteDAEViewSet(viewsets.ModelViewSet):
    queryset = NonConformiteDAE.objects.select_related("ordre_travail", "responsable").all()
    serializer_class = NonConformiteDAESerializer
    permission_classes = [DAE_ENCADREMENT]


class ActionCorrectiveDAEViewSet(viewsets.ModelViewSet):
    queryset = ActionCorrectiveDAE.objects.select_related("non_conformite", "responsable").all()
    serializer_class = ActionCorrectiveDAESerializer
    permission_classes = [DAE_ENCADREMENT]


class AuditQualiteDAEViewSet(viewsets.ModelViewSet):
    queryset = AuditQualiteDAE.objects.all()
    serializer_class = AuditQualiteDAESerializer
    permission_classes = [DAE_ENCADREMENT]


class QualiteKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_qualite_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
