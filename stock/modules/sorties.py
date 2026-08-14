from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import SortieStock, MouvementStock, Alerte
from ..serializers import SortieStockSerializer, SortieStockCreateSerializer


class SortieStockViewSet(viewsets.ModelViewSet):
    queryset = SortieStock.objects.select_related(
        "lot", "lot__article", "utilisateur", "valide_par", "demande_devis"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == "create":
            return SortieStockCreateSerializer
        return SortieStockSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres
        type_sortie = self.request.query_params.get("type_sortie")
        if type_sortie:
            queryset = queryset.filter(type_sortie=type_sortie)
        
        valide = self.request.query_params.get("valide")
        if valide is not None:
            queryset = queryset.filter(valide=valide.lower() == "true")
        
        lot_id = self.request.query_params.get("lot")
        if lot_id:
            queryset = queryset.filter(lot_id=lot_id)
        
        article_id = self.request.query_params.get("article")
        if article_id:
            queryset = queryset.filter(lot__article_id=article_id)
        
        # Filtre par date
        date_debut = self.request.query_params.get("date_debut")
        date_fin = self.request.query_params.get("date_fin")
        if date_debut:
            queryset = queryset.filter(date_sortie__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_sortie__date__lte=date_fin)
        
        return queryset
    
    def perform_create(self, serializer):
        sortie = serializer.save(utilisateur=self.request.user)
        
        # Créer le mouvement de stock pour la traçabilité
        lot = sortie.lot
        article = lot.article
        quantite_avant = lot.quantite_restante
        
        # Mettre à jour le stock du lot
        lot.quantite_restante -= sortie.quantite
        lot.save()
        
        # Mettre à jour le stock de l'article
        article.quantite_stock -= sortie.quantite
        article.save()
        
        # Créer le mouvement de traçabilité
        MouvementStock.objects.create(
            article=article,
            lot=lot,
            type_mouvement="SORTIE",
            quantite=sortie.quantite,
            quantite_avant=quantite_avant,
            quantite_apres=lot.quantite_restante,
            reference_document=sortie.numero_sortie,
            description=f"Sortie de stock: {sortie.get_type_sortie_display()} - {sortie.motif or 'Sans motif'}",
            sortie=sortie,
            utilisateur=self.request.user,
        )
        
        # Vérifier si une alerte doit être créée (stock bas)
        if article.quantite_stock <= article.seuil_alerte:
            niveau = "CRITIQUE" if article.est_critique else "URGENT"
            Alerte.objects.get_or_create(
                titre=f"Stock bas - {article.designation}",
                type_alerte="STOCK_CRITIQUE",
                traitee=False,
                defaults={
                    "message": f"Le stock de {article.designation} ({article.quantite_stock} {article.unite_mesure}) est inférieur au seuil d'alerte ({article.seuil_alerte}).",
                    "niveau_priorite": niveau,
                }
            )
    
    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        """Valider une sortie de stock"""
        sortie = self.get_object()
        
        if sortie.valide:
            return Response(
                {"detail": "Cette sortie est déjà validée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sortie.valide = True
        sortie.valide_par = request.user
        sortie.date_validation = timezone.now()
        sortie.save()
        
        return Response(SortieStockSerializer(sortie).data)
    
    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        """Annuler une sortie de stock (remet le stock)"""
        sortie = self.get_object()
        
        if sortie.valide:
            return Response(
                {"detail": "Impossible d'annuler une sortie déjà validée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lot = sortie.lot
        article = lot.article
        quantite_avant = lot.quantite_restante
        
        # Remettre le stock
        lot.quantite_restante += sortie.quantite
        lot.save()
        
        article.quantite_stock += sortie.quantite
        article.save()
        
        # Créer un mouvement d'annulation
        MouvementStock.objects.create(
            article=article,
            lot=lot,
            type_mouvement="AJUSTEMENT",
            quantite=sortie.quantite,
            quantite_avant=quantite_avant,
            quantite_apres=lot.quantite_restante,
            reference_document=sortie.numero_sortie,
            description=f"Annulation de sortie: {sortie.numero_sortie}",
            utilisateur=request.user,
        )
        
        sortie.delete()
        
        return Response({"detail": "Sortie annulée avec succès."})
