from rest_framework import permissions, viewsets

from .models import Laboratoire
from .serializers import LaboratoireSerializer


class LaboratoireViewSet(viewsets.ModelViewSet):
    queryset = Laboratoire.objects.select_related("responsable").all()
    serializer_class = LaboratoireSerializer
    permission_classes = [permissions.IsAuthenticated]
