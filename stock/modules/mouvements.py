from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import MouvementStock
from ..serializers import MouvementStockSerializer


class MouvementStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter l'historique des mouvements de stock.
    Lecture seule - les mouvements sont créés automatiquement par les autres opérations.
    """
    queryset = MouvementStock.objects.select_related(
        "article", "article__categorie", "lot", "utilisateur", "reception", "sortie", "transfert"
    ).all()
    serializer_class = MouvementStockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres
        type_mouvement = self.request.query_params.get("type_mouvement")
        if type_mouvement:
            queryset = queryset.filter(type_mouvement=type_mouvement)
        
        article_id = self.request.query_params.get("article")
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        
        lot_id = self.request.query_params.get("lot")
        if lot_id:
            queryset = queryset.filter(lot_id=lot_id)
        
        # Filtre par date
        date_debut = self.request.query_params.get("date_debut")
        date_fin = self.request.query_params.get("date_fin")
        if date_debut:
            queryset = queryset.filter(date_mouvement__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_mouvement__date__lte=date_fin)
        
        return queryset
    
    @action(detail=False, methods=["get"])
    def par_article(self, request):
        """Obtenir l'historique des mouvements pour un article spécifique"""
        article_id = request.query_params.get("article_id")
        if not article_id:
            return Response({"detail": "article_id requis"}, status=400)
        
        mouvements = self.get_queryset().filter(article_id=article_id)[:50]
        serializer = self.get_serializer(mouvements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def par_lot(self, request):
        """Obtenir l'historique des mouvements pour un lot spécifique"""
        lot_id = request.query_params.get("lot_id")
        if not lot_id:
            return Response({"detail": "lot_id requis"}, status=400)
        
        mouvements = self.get_queryset().filter(lot_id=lot_id)
        serializer = self.get_serializer(mouvements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def tracabilite_complete(self, request):
        """
        Obtenir la traçabilité complète d'un lot depuis sa réception
        """
        lot_id = request.query_params.get("lot_id")
        if not lot_id:
            return Response({"detail": "lot_id requis"}, status=400)
        
        mouvements = self.get_queryset().filter(lot_id=lot_id).order_by("date_mouvement")
        serializer = self.get_serializer(mouvements, many=True)
        
        return Response({
            "lot_id": lot_id,
            "nombre_mouvements": mouvements.count(),
            "mouvements": serializer.data
        })
