from django.contrib import admin
from .models import *

admin.site.register(UserProfile)


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'acting_username', 'target_username', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('acting_username', 'target_username', 'ip_address')
    readonly_fields = ('action', 'target_user', 'target_username', 'acting_user',
                       'acting_username', 'ip_address', 'user_agent', 'changes', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# --- MODULE AGENDA ---
admin.site.register(RendezVous)
admin.site.register(RendezVousDocument)
admin.site.register(Reunion)
admin.site.register(ReunionPresence)

# --- SITES / GÉOFENCING ---
# Enregistrés explicitement car les paliers (SitePalier) sont prioritaires sur le
# rayon_pointage du site lors de la validation GPS du pointage (voir
# geofencing_utils.get_gps_reference_for_user) mais n'ont aucune interface de
# gestion dédiée côté React — /admin/ reste le seul moyen de les inspecter/
# corriger en dehors de la page "Coordonnées GPS des sites".
@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'latitude', 'longitude', 'rayon_pointage')
    search_fields = ('nom', 'code')


@admin.register(SitePalier)
class SitePalierAdmin(admin.ModelAdmin):
    list_display = ('site', 'nom', 'latitude', 'longitude', 'rayon_pointage', 'est_actif', 'ordre')
    list_filter = ('est_actif', 'site')
    search_fields = ('nom', 'site__nom')

# Register your models here.
