from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Quarantaine
from ..serializers import QuarantaineSerializer


class QuarantaineViewSet(viewsets.ModelViewSet):
    queryset = Quarantaine.objects.select_related(
        "lot", "lot__article", "mis_en_quarantaine_par", "leve_par"
    ).all().order_by("-date_mise_en_quarantaine")
    serializer_class = QuarantaineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        statut = self.request.query_params.get('statut')
        if statut == 'EN_COURS':
            queryset = queryset.filter(levee=False)
        elif statut == 'LEVEE':
            queryset = queryset.filter(levee=True)
        return queryset

    @action(detail=True, methods=["post"], url_path="lever")
    def lever(self, request, pk=None):
        quarantaine = self.get_object()
        quarantaine.levee = True
        quarantaine.date_levee = timezone.now()
        quarantaine.leve_par = request.user
        decision = request.data.get("decision", "")
        commentaire = request.data.get("commentaire", "")
        if decision:
            quarantaine.decision = decision
        if commentaire:
            quarantaine.commentaire = commentaire
        quarantaine.save(update_fields=["levee", "date_levee", "leve_par", "decision", "commentaire"])
        serializer = self.get_serializer(quarantaine)
        return Response(serializer.data)
