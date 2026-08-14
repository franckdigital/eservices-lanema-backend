from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import TransfertInterne
from ..serializers import TransfertInterneSerializer


class TransfertInterneViewSet(viewsets.ModelViewSet):
    queryset = TransfertInterne.objects.select_related(
        "lot",
        "emplacement_source",
        "emplacement_destination",
    ).all().order_by("-date_creation")
    serializer_class = TransfertInterneSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        transfert = self.get_object()
        transfert.valide = True
        transfert.save(update_fields=["valide"])
        serializer = self.get_serializer(transfert)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="executer")
    def executer(self, request, pk=None):
        transfert = self.get_object()
        transfert.execute = True
        transfert.save(update_fields=["execute"])
        serializer = self.get_serializer(transfert)
        return Response(serializer.data)
