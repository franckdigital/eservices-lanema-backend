from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PieceComptable
from .serializers import PieceComptableSerializer


def compute_pieces_kpis(date_debut=None, date_fin=None):
    """Calcule les 5 KPI Pieces comptables de la comptabilite. Reutilisable
    directement par le tableau de bord comptabilite."""
    pieces = PieceComptable.objects.all()
    if date_debut and date_fin:
        pieces = pieces.filter(date_piece__range=(date_debut, date_fin))

    total = pieces.count()
    validees = pieces.filter(statut="VALIDEE")
    en_attente = pieces.filter(statut="ENREGISTREE").count()
    rejetees = pieces.filter(statut="REJETEE").count()

    delais = []
    for piece in validees:
        if piece.date_validation:
            delais.append((piece.date_validation - piece.date_piece).days)
    delai_moyen = round(sum(delais) / len(delais), 1) if delais else None

    taux_validation = round(validees.count() / total * 100, 1) if total else None

    return {
        "nombre_pieces": total,
        "nombre_en_attente": en_attente,
        "nombre_validees": validees.count(),
        "nombre_rejetees": rejetees,
        "taux_validation": taux_validation,
        "delai_moyen_traitement_jours": delai_moyen,
    }


class PieceComptableViewSet(viewsets.ModelViewSet):
    queryset = PieceComptable.objects.select_related("valide_par").all()
    serializer_class = PieceComptableSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        piece = self.get_object()
        role = getattr(getattr(request.user, "client_profile", None), "role", None)
        if role not in {"ADMIN", "GESTIONNAIRE", "COMPTABLE"}:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        piece.statut = "VALIDEE"
        piece.valide_par = request.user
        piece.date_validation = timezone.now().date()
        piece.save(update_fields=["statut", "valide_par", "date_validation"])

        serializer = self.get_serializer(piece)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="rejeter")
    def rejeter(self, request, pk=None):
        piece = self.get_object()
        role = getattr(getattr(request.user, "client_profile", None), "role", None)
        if role not in {"ADMIN", "GESTIONNAIRE", "COMPTABLE"}:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        piece.statut = "REJETEE"
        piece.valide_par = request.user
        piece.date_validation = timezone.now().date()
        piece.save(update_fields=["statut", "valide_par", "date_validation"])

        serializer = self.get_serializer(piece)
        return Response(serializer.data)


class PiecesKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_pieces_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
