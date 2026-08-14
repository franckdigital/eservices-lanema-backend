from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Entrepot, Emplacement
from ..serializers import EntrepotSerializer, EmplacementSerializer


class EntrepotViewSet(viewsets.ModelViewSet):
    queryset = Entrepot.objects.all().order_by("nom")
    serializer_class = EntrepotSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmplacementViewSet(viewsets.ModelViewSet):
    queryset = Emplacement.objects.select_related("entrepot").all().order_by("code")
    serializer_class = EmplacementSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="scan")
    def scan(self, request):
        qr_code = request.data.get("qr_code")
        if not qr_code:
            return Response({"error": "qr_code manquant"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            emplacement = Emplacement.objects.select_related("entrepot").get(code=qr_code)
        except Emplacement.DoesNotExist:
            return Response({"error": "Emplacement introuvable"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(emplacement)
        return Response(serializer.data)
