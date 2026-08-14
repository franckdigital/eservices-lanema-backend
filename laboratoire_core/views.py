from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Activity


class DashboardStatsView(APIView):
    """Vue pour les statistiques principales du dashboard."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from stock.models import MouvementStock, Article, Alerte
        from demandes.models import DemandeDevis
        from facturation.models import Facture
        
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Échantillons en cours (depuis demandes ou stock)
        try:
            echantillons_en_cours = DemandeDevis.objects.filter(
                statut__in=['EN_COURS', 'EN_ATTENTE', 'ACCEPTE']
            ).count()
        except:
            echantillons_en_cours = 0
        
        # Échantillons reçus aujourd'hui
        try:
            echantillons_recus_aujourdhui = DemandeDevis.objects.filter(
                date_creation__date=today
            ).count()
        except:
            echantillons_recus_aujourdhui = 0
        
        # Sorties de stock (remplace essais planifiés)
        try:
            sorties_total = MouvementStock.objects.filter(
                type_mouvement='SORTIE'
            ).count()
            sorties_semaine = MouvementStock.objects.filter(
                type_mouvement='SORTIE',
                date_mouvement__date__gte=week_start
            ).count()
        except:
            sorties_total = 0
            sorties_semaine = 0
        
        # Demandes de devis (remplace non-conformités)
        try:
            demandes_devis = DemandeDevis.objects.filter(
                statut__in=['SOUMIS', 'EN_ATTENTE']
            ).count()
            demandes_en_attente = DemandeDevis.objects.filter(
                statut='EN_ATTENTE'
            ).count()
        except:
            demandes_devis = 0
            demandes_en_attente = 0
        
        # Factures en attente (remplace taux de conformité)
        try:
            factures_en_attente = Facture.objects.filter(
                statut__in=['BROUILLON', 'EMISE', 'EN_ATTENTE']
            ).count()
            factures_montant = Facture.objects.filter(
                statut__in=['BROUILLON', 'EMISE', 'EN_ATTENTE']
            ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        except:
            factures_en_attente = 0
            factures_montant = 0
        
        # Alertes stock
        try:
            alertes_stock = Alerte.objects.filter(traitee=False).count()
        except:
            alertes_stock = 0
        
        data = {
            # Échantillons
            "echantillons_en_cours": echantillons_en_cours,
            "echantillons_recus_aujourdhui": echantillons_recus_aujourdhui,
            # Sorties (remplace essais)
            "sorties_total": sorties_total,
            "sorties_semaine": sorties_semaine,
            # Demandes de devis (remplace non-conformités)
            "demandes_devis": demandes_devis,
            "demandes_en_attente": demandes_en_attente,
            # Factures en attente (remplace taux conformité)
            "factures_en_attente": factures_en_attente,
            "factures_montant": float(factures_montant),
            # Alertes
            "alertes_stock": alertes_stock,
        }
        return Response(data)


class DashboardKPIsView(APIView):
    """Vue pour les KPIs du dashboard."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from stock.models import SortieStock, Article, Alerte, Reception, TransfertInterne
        from demandes.models import DemandeDevis
        from facturation.models import Facture

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Performance hebdomadaire - Demandes d'analyses traitées (uniquement DemandeDevis)
        try:
            demandes_semaine = DemandeDevis.objects.filter(
                created_at__date__gte=week_start
            ).count()
        except:
            demandes_semaine = 0
        
        demandes_objectif = 100
        
        # Performance hebdomadaire - Sorties effectuées (uniquement SortieStock)
        try:
            sorties_semaine = SortieStock.objects.filter(
                date_sortie__date__gte=week_start
            ).count()
        except:
            sorties_semaine = 0
        
        sorties_objectif = 150
        
        # Performance hebdomadaire - Factures payées (statut PAYEE, sans filtre de date)
        try:
            factures_payees = Facture.objects.filter(
                statut='PAYEE'
            ).count()
        except:
            factures_payees = 0
        
        # Total factures pour l'objectif
        try:
            factures_total = Facture.objects.count()
        except:
            factures_total = 0
        
        factures_objectif = max(70, factures_total) if factures_total > 0 else 70
        
        # Réceptions cette semaine (pour les alertes)
        try:
            receptions_semaine = Reception.objects.filter(
                date_reception__gte=week_start
            ).count()
        except:
            receptions_semaine = 0
        
        # Top clients actifs (depuis les fournisseurs des réceptions)
        top_clients = []
        try:
            # D'abord essayer les demandes
            demandes_clients = list(
                DemandeDevis.objects.filter(
                    created_at__date__gte=month_start,
                    client__isnull=False
                ).values('client__client_profile__raison_sociale', 'client__email').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]
            )
            for c in demandes_clients:
                name = c.get('client__client_profile__raison_sociale') or c.get('client__email') or 'Client'
                if name and name != 'Client':
                    top_clients.append({'name': name, 'count': c['count']})
        except:
            pass
        
        # Si pas de clients, utiliser les fournisseurs des réceptions
        if not top_clients:
            try:
                fournisseurs = list(
                    Reception.objects.filter(
                        date_reception__gte=month_start,
                        fournisseur__isnull=False
                    ).values('fournisseur__email', 'fournisseur__first_name', 'fournisseur__last_name').annotate(
                        count=Count('id')
                    ).order_by('-count')[:5]
                )
                for f in fournisseurs:
                    name = f'{f.get("fournisseur__first_name", "")} {f.get("fournisseur__last_name", "")}'.strip()
                    if not name:
                        name = f.get('fournisseur__email', 'Fournisseur')
                    top_clients.append({'name': name, 'count': f['count']})
            except:
                pass
        
        # Alertes dynamiques
        alertes = []
        try:
            # Stock faible
            articles_stock_faible = Article.objects.filter(
                quantite_stock__lte=F('seuil_alerte'),
                seuil_alerte__gt=0
            ).count()
            if articles_stock_faible > 0:
                alertes.append({
                    'type': 'stock_faible',
                    'titre': 'Stock faible',
                    'message': f'{articles_stock_faible} consommables sous le seuil d\'alerte',
                    'couleur': 'blue'
                })
        except:
            pass
        
        try:
            # Alertes non traitées
            alertes_non_traitees = Alerte.objects.filter(traitee=False).count()
            if alertes_non_traitees > 0:
                alertes.append({
                    'type': 'alertes',
                    'titre': 'Alertes en attente',
                    'message': f'{alertes_non_traitees} alertes à traiter',
                    'couleur': 'amber'
                })
        except:
            pass
        
        try:
            # Réceptions cette semaine
            receptions_semaine = Reception.objects.filter(
                date_reception__gte=week_start
            ).count()
            if receptions_semaine > 0:
                alertes.append({
                    'type': 'receptions',
                    'titre': 'Réceptions récentes',
                    'message': f'{receptions_semaine} réceptions cette semaine',
                    'couleur': 'green'
                })
        except:
            pass
        
        data = {
            "performance": {
                "echantillons": {
                    "actuel": demandes_semaine,
                    "objectif": demandes_objectif,
                    "pourcentage": min(100, int(demandes_semaine / demandes_objectif * 100)) if demandes_objectif > 0 else 0
                },
                "sorties": {
                    "actuel": sorties_semaine,
                    "objectif": sorties_objectif,
                    "pourcentage": min(100, int(sorties_semaine / sorties_objectif * 100)) if sorties_objectif > 0 else 0
                },
                "factures": {
                    "actuel": factures_payees,
                    "objectif": factures_objectif,
                    "pourcentage": min(100, int(factures_payees / factures_objectif * 100)) if factures_objectif > 0 else 0
                }
            },
            "top_clients": top_clients,
            "alertes": alertes
        }
        return Response(data)


class DashboardActivitiesView(APIView):
    """Vue pour les activités récentes du dashboard."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from stock.models import MouvementStock, Reception
        from demandes.models import DemandeDevis
        from facturation.models import Facture, Proforma

        limit = int(request.query_params.get('limit', 10))
        activities = []
        
        # Récupérer les dernières demandes de devis
        try:
            demandes = DemandeDevis.objects.select_related('client').order_by('-date_creation')[:limit]
            for d in demandes:
                activities.append({
                    'type': 'DEMANDE',
                    'titre': f'Nouvelle demande de devis',
                    'description': f'Demande #{d.numero} - {d.type_analyse}',
                    'client': (getattr(getattr(d.client, 'client_profile', None), 'raison_sociale', None) or d.client.email) if d.client else 'N/A',
                    'created_at': d.date_creation.isoformat() if d.date_creation else None,
                    'reference': d.numero
                })
        except Exception as e:
            pass
        
        # Récupérer les dernières factures
        try:
            factures = Facture.objects.order_by('-date_creation')[:limit]
            for f in factures:
                activities.append({
                    'type': 'FACTURE',
                    'titre': f'Facture {f.statut}',
                    'description': f'Facture #{f.numero} - {f.montant_ttc}€',
                    'client': 'Client',
                    'created_at': f.date_creation.isoformat() if f.date_creation else None,
                    'reference': f.numero
                })
        except Exception as e:
            pass
        
        # Récupérer les derniers mouvements de stock
        try:
            mouvements = MouvementStock.objects.select_related('lot', 'lot__article').order_by('-date_mouvement')[:limit]
            for m in mouvements:
                type_label = 'Entrée' if m.type_mouvement == 'ENTREE' else 'Sortie'
                activities.append({
                    'type': 'SORTIE' if m.type_mouvement == 'SORTIE' else 'RECEPTION',
                    'titre': f'{type_label} de stock',
                    'description': f'{m.lot.article.designation if m.lot and m.lot.article else "Article"} - Qté: {m.quantite}',
                    'client': m.reference_document or 'N/A',
                    'created_at': m.date_mouvement.isoformat() if m.date_mouvement else None,
                    'reference': m.reference_document or ''
                })
        except Exception as e:
            pass
        
        # Récupérer les dernières réceptions
        try:
            receptions = Reception.objects.order_by('-date_reception')[:limit]
            for r in receptions:
                activities.append({
                    'type': 'RECEPTION',
                    'titre': f'Nouvelle réception',
                    'description': f'Réception #{r.numero_reception}',
                    'client': (getattr(getattr(r.fournisseur, 'client_profile', None), 'raison_sociale', None) or r.fournisseur.email) if getattr(r, 'fournisseur', None) else 'Fournisseur',
                    'created_at': r.date_reception.isoformat() if r.date_reception else None,
                    'reference': r.numero_reception
                })
        except Exception as e:
            pass
        
        # Récupérer les activités du modèle Activity
        try:
            db_activities = Activity.objects.all()[:limit]
            for a in db_activities:
                activities.append({
                    'type': a.type,
                    'titre': a.titre,
                    'description': a.description,
                    'client': a.utilisateur.email if a.utilisateur else 'Système',
                    'created_at': a.created_at.isoformat() if a.created_at else None,
                    'reference': a.reference
                })
        except Exception as e:
            pass
        
        # Trier par date et limiter
        activities.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        activities = activities[:limit]
        
        return Response(activities)
