from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Alerte
from ..serializers import AlerteSerializer


class AlerteViewSet(viewsets.ModelViewSet):
    queryset = Alerte.objects.all().order_by("-date_creation")
    serializer_class = AlerteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        traitee = self.request.query_params.get("traitee")
        if traitee is not None:
            queryset = queryset.filter(traitee=traitee.lower() == "true")

        niveau_priorite = self.request.query_params.get("niveau_priorite")
        if niveau_priorite:
            queryset = queryset.filter(niveau_priorite=niveau_priorite)

        type_alerte = self.request.query_params.get("type_alerte")
        if type_alerte:
            queryset = queryset.filter(type_alerte=type_alerte)

        return queryset

    @action(detail=True, methods=["post"], url_path="marquer_traitee")
    def marquer_traitee(self, request, pk=None):
        alerte = self.get_object()
        commentaire = request.data.get("commentaire", "")
        alerte.traitee = True
        if commentaire:
            alerte.commentaire = commentaire
        alerte.date_traitement = timezone.now()
        alerte.traite_par = request.user
        alerte.save(update_fields=["traitee", "commentaire", "date_traitement", "traite_par"])
        serializer = self.get_serializer(alerte)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="critiques")
    def critiques(self, request):
        qs = self.get_queryset().filter(niveau_priorite="CRITIQUE", traitee=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
