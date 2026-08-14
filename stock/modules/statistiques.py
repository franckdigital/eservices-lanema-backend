from datetime import timedelta
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Article, Lot, Alerte, Quarantaine, Reception, SortieStock, MouvementStock


class StockStatistiquesView(APIView):
    """Statistiques détaillées du stock"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Stats générales
        total_articles = Article.objects.count()
        total_lots = Lot.objects.count()
        lots_ouverts = Lot.objects.filter(ouvert=True).count()
        
        # Alertes
        alertes_actives = Alerte.objects.filter(traitee=False).count()
        alertes_critiques = Alerte.objects.filter(traitee=False, niveau_priorite="CRITIQUE").count()
        alertes_urgentes = Alerte.objects.filter(traitee=False, niveau_priorite="URGENT").count()
        
        # Quarantaines
        lots_en_quarantaine = Quarantaine.objects.filter(levee=False).count()
        
        # Péremption
        dans_7_jours = today + timedelta(days=7)
        dans_30_jours = today + timedelta(days=30)
        dans_60_jours = today + timedelta(days=60)
        
        lots_expires = Lot.objects.filter(
            date_peremption__lt=today,
            quantite_restante__gt=0
        ).count()
        
        lots_expirent_7j = Lot.objects.filter(
            date_peremption__gte=today,
            date_peremption__lte=dans_7_jours,
            quantite_restante__gt=0
        ).count()
        
        lots_expirent_30j = Lot.objects.filter(
            date_peremption__gte=today,
            date_peremption__lte=dans_30_jours,
            quantite_restante__gt=0
        ).count()
        
        # Stock critique
        articles_stock_critique = Article.objects.filter(
            quantite_stock__lte=F("seuil_alerte")
        ).count()
        
        articles_rupture = Article.objects.filter(quantite_stock=0).count()
        
        # Valeur du stock (si prix disponible)
        valeur_totale_lots = Lot.objects.filter(
            quantite_restante__gt=0
        ).aggregate(total=Sum("quantite_restante"))["total"] or 0
        
        # Articles par catégorie
        articles_par_categorie = list(
            Article.objects.values('categorie__nom')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        articles_par_categorie = [
            {"categorie": item['categorie__nom'] or 'Sans catégorie', "count": item['count']}
            for item in articles_par_categorie
        ]
        
        # Lots par statut
        lots_actifs = Lot.objects.filter(quantite_restante__gt=0, ouvert=False).count()
        lots_statuts = [
            {"statut": "ACTIF", "count": lots_actifs},
            {"statut": "OUVERT", "count": lots_ouverts},
            {"statut": "EXPIRE", "count": lots_expires},
        ]
        
        data = {
            # Format plat pour le frontend
            "total_articles": total_articles,
            "total_lots": total_lots,
            "lots_ouverts": lots_ouverts,
            "valeur_stock_estimee": valeur_totale_lots,
            "articles_par_categorie": articles_par_categorie,
            "lots_par_statut": lots_statuts,
            # Format imbriqué (conservé pour compatibilité)
            "general": {
                "total_articles": total_articles,
                "total_lots": total_lots,
                "lots_ouverts": lots_ouverts,
                "valeur_totale_stock": valeur_totale_lots,
            },
            "alertes": {
                "total_actives": alertes_actives,
                "critiques": alertes_critiques,
                "urgentes": alertes_urgentes,
            },
            "quarantaines": {
                "lots_en_quarantaine": lots_en_quarantaine,
            },
            "peremption": {
                "lots_expires": lots_expires,
                "expirent_7_jours": lots_expirent_7j,
                "expirent_30_jours": lots_expirent_30j,
            },
            "stock": {
                "articles_stock_critique": articles_stock_critique,
                "articles_en_rupture": articles_rupture,
            },
        }
        
        return Response(data)


class MouvementsStatistiquesView(APIView):
    """Statistiques des mouvements de stock"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from ..models import TransfertInterne
        
        today = timezone.now().date()
        
        # Période demandée (en jours)
        jours = int(request.query_params.get("jours", 30))
        date_debut = today - timedelta(days=jours)
        
        # Compter les réceptions (Entrées) - date_reception est un DateField
        entrees_count = Reception.objects.filter(
            date_reception__gte=date_debut
        ).count()
        # Quantité entrée via les lignes de réception
        from ..models import LigneReception
        entrees_quantite = LigneReception.objects.filter(
            reception__date_reception__gte=date_debut
        ).aggregate(total=Sum("quantite_recue"))["total"] or 0
        
        # Compter les sorties - date_sortie est un DateTimeField
        sorties_count = SortieStock.objects.filter(
            date_sortie__gte=date_debut
        ).count()
        sorties_quantite = SortieStock.objects.filter(
            date_sortie__gte=date_debut
        ).aggregate(total=Sum("quantite"))["total"] or 0
        
        # Compter les transferts - date_creation est un DateTimeField
        transferts_count = TransfertInterne.objects.filter(
            date_creation__gte=date_debut
        ).count()
        transferts_quantite = TransfertInterne.objects.filter(
            date_creation__gte=date_debut
        ).aggregate(total=Sum("quantite"))["total"] or 0
        
        # Ajustements (via MouvementStock si disponible)
        ajustements_count = MouvementStock.objects.filter(
            date_mouvement__gte=date_debut,
            type_mouvement="AJUSTEMENT"
        ).count()
        ajustements_quantite = MouvementStock.objects.filter(
            date_mouvement__gte=date_debut,
            type_mouvement="AJUSTEMENT"
        ).aggregate(total=Sum("quantite"))["total"] or 0
        
        total_mouvements = entrees_count + sorties_count + transferts_count + ajustements_count
        
        # Mouvements par type pour affichage
        mouvements_par_type = [
            {"type_mouvement": "ENTREE", "count": entrees_count, "quantite_totale": entrees_quantite},
            {"type_mouvement": "SORTIE", "count": sorties_count, "quantite_totale": sorties_quantite},
            {"type_mouvement": "TRANSFERT", "count": transferts_count, "quantite_totale": transferts_quantite},
            {"type_mouvement": "AJUSTEMENT", "count": ajustements_count, "quantite_totale": ajustements_quantite},
        ]
        
        # Évolution journalière - combinée des différentes sources
        evolution_journaliere = []
        
        # Entrées par jour (depuis les réceptions) - date_reception est un DateField
        receptions_par_jour = list(
            Reception.objects.filter(
                date_reception__gte=date_debut
            ).values("date_reception").annotate(
                count=Count("id")
            ).order_by("date_reception")
        )
        for item in receptions_par_jour:
            evolution_journaliere.append({
                "date": item["date_reception"].isoformat() if item["date_reception"] else None,
                "type_mouvement": "ENTREE",
                "count": item["count"],
                "quantite": 0
            })
        
        # Sorties par jour
        sorties_par_jour = list(
            SortieStock.objects.filter(
                date_sortie__gte=date_debut
            ).annotate(
                date=TruncDate("date_sortie")
            ).values("date").annotate(
                count=Count("id"),
                quantite=Sum("quantite")
            ).order_by("date")
        )
        for item in sorties_par_jour:
            evolution_journaliere.append({
                "date": item["date"].isoformat() if item["date"] else None,
                "type_mouvement": "SORTIE",
                "count": item["count"],
                "quantite": item["quantite"] or 0
            })
        
        data = {
            "total_mouvements": total_mouvements,
            "entrees": {
                "nombre": entrees_count,
                "quantite": entrees_quantite,
            },
            "sorties": {
                "nombre": sorties_count,
                "quantite": sorties_quantite,
            },
            "transferts": transferts_count,
            "ajustements": ajustements_count,
            "mouvements_par_type": mouvements_par_type,
            "evolution_journaliere": evolution_journaliere,
        }
        
        return Response(data)


class SortiesStatistiquesView(APIView):
    """Statistiques des sorties de stock"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        
        periode = request.query_params.get("periode", "mois")
        if periode == "semaine":
            date_debut = today - timedelta(days=7)
        elif periode == "annee":
            date_debut = today.replace(month=1, day=1)
        else:
            date_debut = debut_mois
        
        # Sorties par type
        sorties_par_type = list(
            SortieStock.objects.filter(
                date_sortie__date__gte=date_debut
            ).values("type_sortie").annotate(
                count=Count("id"),
                quantite_totale=Sum("quantite")
            )
        )
        
        # Sorties validées vs en attente
        sorties_validees = SortieStock.objects.filter(
            date_sortie__date__gte=date_debut,
            valide=True
        ).count()
        
        sorties_en_attente = SortieStock.objects.filter(
            date_sortie__date__gte=date_debut,
            valide=False
        ).count()
        
        # Top articles sortis
        top_articles_sortis = list(
            SortieStock.objects.filter(
                date_sortie__date__gte=date_debut
            ).values(
                "lot__article__id",
                "lot__article__designation",
                "lot__article__reference_interne"
            ).annotate(
                nb_sorties=Count("id"),
                quantite_totale=Sum("quantite")
            ).order_by("-quantite_totale")[:10]
        )
        
        # Évolution journalière des sorties
        evolution_sorties = list(
            SortieStock.objects.filter(
                date_sortie__date__gte=date_debut
            ).annotate(
                date=TruncDate("date_sortie")
            ).values("date").annotate(
                count=Count("id"),
                quantite=Sum("quantite")
            ).order_by("date")
        )
        
        data = {
            "periode": periode,
            "date_debut": date_debut.isoformat(),
            "date_fin": today.isoformat(),
            "sorties_par_type": sorties_par_type,
            "sorties_validees": sorties_validees,
            "sorties_en_attente": sorties_en_attente,
            "top_articles_sortis": top_articles_sortis,
            "evolution_journaliere": evolution_sorties,
        }
        
        return Response(data)


class TableauBordCompletView(APIView):
    """Vue complète du tableau de bord avec toutes les statistiques"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        dans_7_jours = today + timedelta(days=7)
        dans_30_jours = today + timedelta(days=30)
        debut_mois = today.replace(day=1)
        
        # Statistiques générales
        stats = {
            "total_articles": Article.objects.count(),
            "total_lots": Lot.objects.count(),
            "alertes_actives": Alerte.objects.filter(traitee=False).count(),
            "produits_expires": Lot.objects.filter(
                date_peremption__lt=today,
                quantite_restante__gt=0
            ).count(),
            "stock_critique": Article.objects.filter(
                quantite_stock__lte=F("seuil_alerte"),
                quantite_stock__gt=0
            ).count(),
            "articles_en_rupture": Article.objects.filter(quantite_stock=0).count(),
            "lots_en_quarantaine": Quarantaine.objects.filter(levee=False).count(),
            "expirent_bientot": Lot.objects.filter(
                date_peremption__gte=today,
                date_peremption__lte=dans_30_jours,
                quantite_restante__gt=0
            ).count(),
        }
        
        # Activité du mois
        activite_mois = {
            "receptions": Reception.objects.filter(date_reception__gte=debut_mois).count(),
            "sorties": SortieStock.objects.filter(date_sortie__date__gte=debut_mois).count(),
            "mouvements_total": MouvementStock.objects.filter(date_mouvement__date__gte=debut_mois).count(),
        }
        
        # Alertes critiques (top 5)
        alertes_critiques = list(
            Alerte.objects.filter(
                traitee=False
            ).order_by(
                "-niveau_priorite", "-date_creation"
            ).values(
                "id", "titre", "message", "type_alerte", "niveau_priorite", "date_creation"
            )[:5]
        )
        
        # Lots expirant bientôt (top 5)
        lots_expirant = list(
            Lot.objects.filter(
                date_peremption__gte=today,
                date_peremption__lte=dans_30_jours,
                quantite_restante__gt=0
            ).select_related("article").values(
                "id",
                "numero_lot",
                "article__designation",
                "date_peremption",
                "quantite_restante",
                "unite"
            ).order_by("date_peremption")[:5]
        )
        
        # Dernières sorties
        dernieres_sorties = list(
            SortieStock.objects.select_related(
                "lot", "lot__article", "utilisateur"
            ).order_by("-date_sortie").values(
                "id",
                "numero_sortie",
                "lot__article__designation",
                "quantite",
                "type_sortie",
                "date_sortie",
                "valide"
            )[:5]
        )
        
        return Response({
            "stats": stats,
            "activite_mois": activite_mois,
            "alertes_critiques": alertes_critiques,
            "lots_expirant_bientot": lots_expirant,
            "dernieres_sorties": dernieres_sorties,
        })
