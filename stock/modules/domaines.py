from rest_framework import permissions, viewsets

from ..models import Domaine, CategorieArticle
from ..serializers import DomaineSerializer, CategorieArticleSerializer


class DomaineViewSet(viewsets.ModelViewSet):
    queryset = Domaine.objects.all().order_by("code")
    serializer_class = DomaineSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategorieArticleViewSet(viewsets.ModelViewSet):
    queryset = CategorieArticle.objects.all().order_by("code")
    serializer_class = CategorieArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
