from rest_framework import permissions, viewsets

from ..models import Article
from ..serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by("reference_interne")
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
