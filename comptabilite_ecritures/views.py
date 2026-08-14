from django.db.models import Count, Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CompteComptable, EcritureComptable, JournalComptable
from .serializers import CompteComptableSerializer, EcritureComptableSerializer, JournalComptableSerializer


def compute_ecritures_kpis(date_debut=None, date_fin=None):
    """Calcule les 5 KPI Ecritures comptables de la comptabilite. Reutilisable
    directement par le tableau de bord comptabilite."""
    ecritures = EcritureComptable.objects.all()
    if date_debut and date_fin:
        ecritures = ecritures.filter(date_ecriture__range=(date_debut, date_fin))

    total = ecritures.count()
    validees = ecritures.filter(valide=True).count()
    montant_total = ecritures.aggregate(t=Sum("montant"))["t"] or 0

    par_journal = list(
        ecritures.values("journal__code").annotate(nombre=Count("id")).order_by("-nombre")
    )

    taux_validation = round(validees / total * 100, 1) if total else None

    return {
        "nombre_ecritures": total,
        "nombre_ecritures_validees": validees,
        "montant_total": float(montant_total),
        "repartition_par_journal": par_journal,
        "taux_validation": taux_validation,
    }


class CompteComptableViewSet(viewsets.ModelViewSet):
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    permission_classes = [permissions.IsAuthenticated]


class JournalComptableViewSet(viewsets.ModelViewSet):
    queryset = JournalComptable.objects.all()
    serializer_class = JournalComptableSerializer
    permission_classes = [permissions.IsAuthenticated]


class EcritureComptableViewSet(viewsets.ModelViewSet):
    queryset = EcritureComptable.objects.select_related("journal", "compte_debit", "compte_credit", "piece").all()
    serializer_class = EcritureComptableSerializer
    permission_classes = [permissions.IsAuthenticated]


class EcrituresKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_ecritures_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
