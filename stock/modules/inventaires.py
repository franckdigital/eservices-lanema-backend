from django.utils import timezone
from django.db.models import Sum
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Inventaire, LigneInventaire, Article, Lot, MouvementStock
from ..serializers import (
    InventaireSerializer,
    InventaireCreateSerializer,
    LigneInventaireSerializer,
)


class InventaireViewSet(viewsets.ModelViewSet):
    queryset = Inventaire.objects.select_related(
        "entrepot", "responsable"
    ).prefetch_related("lignes").all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == "create":
            return InventaireCreateSerializer
        return InventaireSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        statut = self.request.query_params.get("statut")
        if statut:
            queryset = queryset.filter(statut=statut)
        
        type_inv = self.request.query_params.get("type_inventaire")
        if type_inv:
            queryset = queryset.filter(type_inventaire=type_inv)
        
        entrepot_id = self.request.query_params.get("entrepot")
        if entrepot_id:
            queryset = queryset.filter(entrepot_id=entrepot_id)
        
        return queryset
    
    def perform_create(self, serializer):
        inventaire = serializer.save(responsable=self.request.user)
        
        # Générer automatiquement les lignes d'inventaire basées sur les articles/lots
        entrepot = inventaire.entrepot
        
        if entrepot:
            # Inventaire pour un entrepôt spécifique
            lots = Lot.objects.filter(
                quantite_restante__gt=0
            ).select_related("article")
        else:
            # Inventaire complet de tous les lots
            lots = Lot.objects.filter(
                quantite_restante__gt=0
            ).select_related("article")
        
        for lot in lots:
            LigneInventaire.objects.create(
                inventaire=inventaire,
                article=lot.article,
                lot=lot,
                quantite_theorique=lot.quantite_restante,
            )
    
    @action(detail=True, methods=["post"])
    def demarrer(self, request, pk=None):
        """Démarrer un inventaire planifié"""
        inventaire = self.get_object()
        
        if inventaire.statut != "PLANIFIE":
            return Response(
                {"detail": "Seul un inventaire planifié peut être démarré."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventaire.statut = "EN_COURS"
        inventaire.save()
        
        return Response(InventaireSerializer(inventaire).data)
    
    @action(detail=True, methods=["post"])
    def terminer(self, request, pk=None):
        """Terminer un inventaire en cours"""
        inventaire = self.get_object()
        
        if inventaire.statut != "EN_COURS":
            return Response(
                {"detail": "Seul un inventaire en cours peut être terminé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que toutes les lignes ont été comptées
        lignes_non_comptees = inventaire.lignes.filter(quantite_comptee__isnull=True).count()
        if lignes_non_comptees > 0:
            return Response(
                {"detail": f"{lignes_non_comptees} ligne(s) n'ont pas encore été comptées."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventaire.statut = "TERMINE"
        inventaire.date_fin = timezone.now()
        inventaire.save()
        
        return Response(InventaireSerializer(inventaire).data)
    
    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        """Valider un inventaire terminé et appliquer les ajustements"""
        inventaire = self.get_object()
        
        if inventaire.statut != "TERMINE":
            return Response(
                {"detail": "Seul un inventaire terminé peut être validé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Appliquer les ajustements de stock
        for ligne in inventaire.lignes.filter(quantite_comptee__isnull=False):
            if ligne.ecart != 0 and ligne.lot:
                lot = ligne.lot
                article = ligne.article
                quantite_avant = lot.quantite_restante
                
                # Mettre à jour le lot
                lot.quantite_restante = ligne.quantite_comptee
                lot.save()
                
                # Mettre à jour l'article
                article.quantite_stock = article.quantite_stock + ligne.ecart
                article.save()
                
                # Créer un mouvement de traçabilité
                MouvementStock.objects.create(
                    article=article,
                    lot=lot,
                    type_mouvement="AJUSTEMENT",
                    quantite=abs(ligne.ecart),
                    quantite_avant=quantite_avant,
                    quantite_apres=ligne.quantite_comptee,
                    reference_document=inventaire.numero_inventaire,
                    description=f"Ajustement inventaire: {ligne.commentaire or 'Écart constaté'}",
                    utilisateur=request.user,
                )
        
        inventaire.statut = "VALIDE"
        inventaire.save()
        
        return Response(InventaireSerializer(inventaire).data)
    
    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        """Annuler un inventaire"""
        inventaire = self.get_object()
        
        if inventaire.statut == "VALIDE":
            return Response(
                {"detail": "Un inventaire validé ne peut pas être annulé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventaire.statut = "ANNULE"
        inventaire.save()
        
        return Response(InventaireSerializer(inventaire).data)
    
    @action(detail=True, methods=["get"])
    def lignes(self, request, pk=None):
        """Obtenir les lignes d'un inventaire"""
        inventaire = self.get_object()
        lignes = inventaire.lignes.select_related("article", "lot", "emplacement", "compte_par").all()
        serializer = LigneInventaireSerializer(lignes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def compter_ligne(self, request, pk=None):
        """Enregistrer le comptage d'une ligne"""
        inventaire = self.get_object()
        
        if inventaire.statut != "EN_COURS":
            return Response(
                {"detail": "L'inventaire doit être en cours pour enregistrer un comptage."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ligne_id = request.data.get("ligne_id")
        quantite_comptee = request.data.get("quantite_comptee")
        commentaire = request.data.get("commentaire", "")
        
        if ligne_id is None or quantite_comptee is None:
            return Response(
                {"detail": "ligne_id et quantite_comptee sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ligne = inventaire.lignes.get(id=ligne_id)
        except LigneInventaire.DoesNotExist:
            return Response(
                {"detail": "Ligne non trouvée."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        ligne.quantite_comptee = float(quantite_comptee)
        ligne.commentaire = commentaire
        ligne.compte_par = request.user
        ligne.date_comptage = timezone.now()
        ligne.save()
        
        return Response(LigneInventaireSerializer(ligne).data)
    
    @action(detail=True, methods=["get"])
    def resume(self, request, pk=None):
        """Obtenir un résumé de l'inventaire"""
        inventaire = self.get_object()
        
        lignes = inventaire.lignes.all()
        lignes_comptees = lignes.filter(quantite_comptee__isnull=False)
        
        ecarts_positifs = lignes_comptees.filter(ecart__gt=0).aggregate(total=Sum("ecart"))["total"] or 0
        ecarts_negatifs = lignes_comptees.filter(ecart__lt=0).aggregate(total=Sum("ecart"))["total"] or 0
        
        return Response({
            "numero_inventaire": inventaire.numero_inventaire,
            "statut": inventaire.statut,
            "total_lignes": lignes.count(),
            "lignes_comptees": lignes_comptees.count(),
            "lignes_restantes": lignes.filter(quantite_comptee__isnull=True).count(),
            "ecarts_positifs": ecarts_positifs,
            "ecarts_negatifs": ecarts_negatifs,
            "ecart_total": ecarts_positifs + ecarts_negatifs,
            "progression": round((lignes_comptees.count() / lignes.count() * 100) if lignes.count() > 0 else 0, 1),
        })


class LigneInventaireViewSet(viewsets.ModelViewSet):
    queryset = LigneInventaire.objects.select_related(
        "inventaire", "article", "lot", "emplacement", "compte_par"
    ).all()
    serializer_class = LigneInventaireSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        inventaire_id = self.request.query_params.get("inventaire")
        if inventaire_id:
            queryset = queryset.filter(inventaire_id=inventaire_id)
        
        non_comptees = self.request.query_params.get("non_comptees")
        if non_comptees and non_comptees.lower() == "true":
            queryset = queryset.filter(quantite_comptee__isnull=True)
        
        avec_ecart = self.request.query_params.get("avec_ecart")
        if avec_ecart and avec_ecart.lower() == "true":
            queryset = queryset.exclude(ecart=0)
        
        return queryset
