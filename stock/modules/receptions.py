from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import LigneReception, Reception
from ..serializers import LigneReceptionSerializer, ReceptionSerializer


class ReceptionViewSet(viewsets.ModelViewSet):
    queryset = Reception.objects.all().order_by("-date_reception")
    serializer_class = ReceptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="verifier")
    def verifier(self, request, pk=None):
        reception = self.get_object()
        serializer = self.get_serializer(reception)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        reception = self.get_object()
        conforme = request.data.get("conforme")
        if conforme is not None:
            reception.conforme = bool(conforme)
            reception.save(update_fields=["conforme"])
        serializer = self.get_serializer(reception)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="lignes")
    def lignes(self, request, pk=None):
        reception = self.get_object()
        if request.method.lower() == "get":
            lignes = reception.lignes.all()
            serializer = LigneReceptionSerializer(lignes, many=True)
            return Response(serializer.data)

        data = request.data.copy()
        data["reception"] = reception.id
        serializer = LigneReceptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
