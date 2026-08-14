from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import CertificatDMCT, InstrumentMesure
from .serializers import CertificatDMCTSerializer, InstrumentMesureSerializer

DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_instruments_kpis(date_debut=None, date_fin=None):
    """Calcule les 9 KPI Instruments de mesure (categorie 2) de la DMCT.
    Reutilisable directement par le tableau de bord DMCT."""
    from dmct_prestations.models import PrestationDMCT

    prestations = PrestationDMCT.objects.filter(statut="TERMINEE")
    if date_debut and date_fin:
        prestations = prestations.filter(date_fin__date__range=(date_debut, date_fin))

    certificats = CertificatDMCT.objects.all()
    if date_debut and date_fin:
        certificats = certificats.filter(date_emission__range=(date_debut, date_fin))

    prestations_avec_instrument = prestations.filter(instrument__isnull=False).select_related("instrument")
    dernieres_par_instrument = {}
    for p in prestations_avec_instrument.order_by("date_fin"):
        dernieres_par_instrument[p.instrument_id] = p.conforme

    nb_conformes = sum(1 for c in dernieres_par_instrument.values() if c is True)
    nb_non_conformes = sum(1 for c in dernieres_par_instrument.values() if c is False)
    total_evalues = nb_conformes + nb_non_conformes
    taux_conformite = round(nb_conformes / total_evalues * 100, 1) if total_evalues else None

    return {
        "nombre_instruments_controles": prestations.filter(type_prestation="CONTROLE").count(),
        "nombre_instruments_etalonnes": prestations.filter(type_prestation="ETALONNAGE").count(),
        "nombre_instruments_verifies": prestations.filter(type_prestation="VERIFICATION").count(),
        "nombre_instruments_certifies": prestations.filter(type_prestation="CERTIFICATION").count(),
        "nombre_instruments_conformes": nb_conformes,
        "nombre_instruments_non_conformes": nb_non_conformes,
        "taux_conformite_instruments": taux_conformite,
        "nombre_instruments_immobilises": InstrumentMesure.objects.filter(statut="IMMOBILISE").count(),
        "nombre_certificats_delivres": certificats.count(),
    }


class InstrumentMesureViewSet(viewsets.ModelViewSet):
    queryset = InstrumentMesure.objects.select_related("client").all()
    serializer_class = InstrumentMesureSerializer
    permission_classes = [DMCT_ENCADREMENT]


class CertificatDMCTViewSet(viewsets.ModelViewSet):
    queryset = CertificatDMCT.objects.select_related("instrument").all()
    serializer_class = CertificatDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class InstrumentsKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_instruments_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
