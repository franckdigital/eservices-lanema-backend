from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Lot
from ..serializers import LotSerializer


class LotViewSet(viewsets.ModelViewSet):
    queryset = Lot.objects.select_related("article").all().order_by("numero_lot")
    serializer_class = LotSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="scan")
    def scan(self, request):
        qr_code = request.data.get("qr_code")
        if not qr_code:
            return Response({"error": "qr_code manquant"}, status=status.HTTP_400_BAD_REQUEST)
        # Pour l'instant, on mappe un QR code directement sur numero_lot
        try:
            lot = Lot.objects.select_related("article").get(numero_lot=qr_code)
        except Lot.DoesNotExist:
            return Response({"error": "Lot introuvable"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(lot)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="marquer_ouvert")
    def marquer_ouvert(self, request, pk=None):
        lot = self.get_object()
        lot.ouvert = True
        lot.save(update_fields=["ouvert"])
        serializer = self.get_serializer(lot)
        return Response(serializer.data)
