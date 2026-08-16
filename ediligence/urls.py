"""
URL configuration for ediligence project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse

def api_home(request):
    """Page d'accueil de l'API"""
    return JsonResponse({
        'message': 'Bienvenue sur l\'API Ediligence',
        'version': '1.0',
        'endpoints': {
            # Administration
            'admin': '/admin/',
            'api_root': '/api/',
            
            # Authentification
            'auth_login': '/api/auth/login/',
            'auth_register': '/api/auth/register/',
            'auth_me': '/api/auth/me/',
            'auth_change_password': '/api/auth/change-password/',
            'token': '/api/token/',
            'token_refresh': '/api/token/refresh/',
            
            # Gestion des utilisateurs
            'users': '/api/users/',
            'directions': '/api/directions/',
            'services': '/api/services/',
            
            # Courriers et diligences
            'courriers': '/api/courriers/',
            'courrier_access': '/api/courrier-access/',
            'courrier_imputation': '/api/courrier-imputation/',
            'diligences': '/api/diligences/',
            'enhanced_diligences': '/api/enhanced-diligences/',
            'diligence_documents': '/api/diligence-documents/',
            'diligence_notifications': '/api/diligence-notifications/',
            
            # Congés et absences
            'demandes_conge': '/api/demandes-conge/',
            'demandes_absence': '/api/demandes-absence/',
            
            # Projets et tâches
            'activites': '/api/activites/',
            'domaines': '/api/domaines/',
            'projets': '/api/projets/',
            'taches': '/api/taches/',
            'commentaires': '/api/commentaires/',
            'fichiers': '/api/fichiers/',
            
            # Présences et bureaux
            'presences': '/api/presences/',
            'bureaux': '/api/bureaux/',
            'presence_stats': '/api/stats/presence/',
            
            # Notifications et permissions
            'notifications': '/api/notifications/',
            'role_permissions': '/api/role-permissions/',
            
            # Imputation et accès
            'imputation_files': '/api/imputation-files/',
            'imputation_access': '/api/imputation-access/',
            'user_diligence_comments': '/api/user-diligence-comments/',
            'user_diligence_instructions': '/api/user-diligence-instructions/',
            
            # Module Gestion de Projets
            'module_projets': '/api/projet/projets/',
            'module_taches': '/api/projet/taches/',
            'module_sous_taches': '/api/projet/sous-taches/',
            'module_commentaires_tache': '/api/projet/commentaires/',
            'module_pieces_jointes': '/api/projet/pieces-jointes/',
            'module_livrables': '/api/projet/livrables/',
            'module_validations': '/api/projet/validations/',
            'module_notifications_projet': '/api/projet/notifications/',
            'module_historique': '/api/projet/historique/',
            'module_dashboard': '/api/projet/dashboard/',
            'module_kanban': '/api/projet/taches/kanban/',
            'module_gantt': '/api/projet/projets/{id}/gantt/',
            'module_rapport_projet': '/api/projet/rapports/projet/{id}/',
            'module_rapport_agent': '/api/projet/rapports/agent/{id}/',
            'module_detecter_retards': '/api/projet/detecter-retards/',
            
        }
    })

urlpatterns = [
    path('', api_home, name='api_home'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/projet/', include('projet.urls')),

    # Modules laboratoire (importes depuis laboratoire-backend), namespaces sous
    # /api/labo/ pour eviter toute collision avec les routes existantes ci-dessus
    # (ex: /api/notifications/ existe deja via core.urls).
    path('api/labo/clients/', include('clients.urls')),
    path('api/labo/stock/', include('stock.urls')),
    path('api/labo/demandes/', include('demandes.urls')),
    path('api/labo/facturation/', include('facturation.urls')),
    path('api/labo/metrologie/', include('metrologie.urls')),
    path('api/labo/qualite/', include('qualite.urls')),
    path('api/labo/reporting/', include('reporting.urls')),
    path('api/labo/notifications/', include('notifications.urls')),
    path('api/labo/landing/', include('landing.urls')),
    path('api/labo/core/', include('laboratoire_core.urls')),
    path('api/laboratoires/', include('laboratoires.urls')),
    path('api/dea/', include('dea_dashboard.urls')),

    # KPI decisionnels DG (services rattaches a la Direction Generale)
    path('api/dg/communication/', include('dg_communication.urls')),
    path('api/dg/patrimoine/', include('dg_patrimoine.urls')),
    path('api/dg/qualite/', include('dg_qualite.urls')),
    path('api/dg/juridique/', include('dg_juridique.urls')),
    path('api/dg/', include('dg_dashboard.urls')),

    # KPI decisionnels DAAF (Direction Administrative et des Affaires Financieres)
    path('api/daaf/finance/', include('daaf_finance.urls')),
    path('api/daaf/achats/', include('daaf_achats.urls')),
    path('api/daaf/moyens-generaux/', include('daaf_moyens_generaux.urls')),
    path('api/daaf/stock/', include('daaf_stock.urls')),
    path('api/daaf/', include('daaf_dashboard.urls')),

    # KPI decisionnels DAE (Direction de l'Aeronautique)
    path('api/dae/clients/', include('aero_clients.urls')),
    path('api/dae/stock/', include('aero_stock.urls')),
    path('api/dae/maintenance/', include('aero_maintenance.urls')),
    path('api/dae/qualite/', include('aero_qualite.urls')),
    path('api/dae/securite/', include('aero_securite.urls')),
    path('api/dae/atelier/', include('aero_atelier.urls')),
    path('api/dae/finance/', include('aero_finance.urls')),
    path('api/dae/portail-client/', include('aero_clients.portal_urls')),
    path('api/dae/', include('aero_dashboard.urls')),

    # KPI decisionnels DMCT (Direction de la Metrologie et des Controles Techniques)
    path('api/dmct/clients/', include('dmct_clients.urls')),
    path('api/dmct/demandes/', include('dmct_demandes.urls')),
    path('api/dmct/instruments/', include('dmct_instruments.urls')),
    path('api/dmct/prestations/', include('dmct_prestations.urls')),
    path('api/dmct/qualite/', include('dmct_qualite.urls')),
    path('api/dmct/equipements-rh/', include('dmct_equipements_rh.urls')),
    path('api/dmct/inspections/', include('dmct_inspections.urls')),
    path('api/dmct/finance/', include('dmct_finance.urls')),
    path('api/dmct/', include('dmct_dashboard.urls')),

    # KPI decisionnels DFIR (Direction Formation, Innovation et Recherche)
    path('api/dfir/participants/', include('dfir_participants.urls')),
    path('api/dfir/formateurs/', include('dfir_formateurs.urls')),
    path('api/dfir/formations/', include('dfir_formations.urls')),
    path('api/dfir/innovation/', include('dfir_innovation.urls')),
    path('api/dfir/recherche/', include('dfir_recherche.urls')),
    path('api/dfir/assistance/', include('dfir_assistance.urls')),
    path('api/dfir/qualite/', include('dfir_qualite.urls')),
    path('api/dfir/finance/', include('dfir_finance.urls')),
    path('api/dfir/elearning/', include('dfir_elearning.urls')),
    path('api/dfir/email/', include('dfir_email.urls')),
    path('api/dfir/', include('dfir_dashboard.urls')),

    # Module Comptabilite (transverse) + Agent Comptable du Tresor
    path('api/comptabilite/fournisseurs/', include('comptabilite_fournisseurs.urls')),
    path('api/comptabilite/tresorerie/', include('comptabilite_tresorerie.urls')),
    path('api/comptabilite/caisse/', include('comptabilite_caisse.urls')),
    path('api/comptabilite/pieces/', include('comptabilite_pieces.urls')),
    path('api/comptabilite/ecritures/', include('comptabilite_ecritures.urls')),
    path('api/comptabilite/', include('comptabilite_dashboard.urls')),
]

# Servir les fichiers média (dev + production via Django)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
