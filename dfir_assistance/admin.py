from django.contrib import admin

from .models import MissionAssistance


@admin.register(MissionAssistance)
class MissionAssistanceAdmin(admin.ModelAdmin):
    list_display = ["reference", "entreprise", "statut", "date_demande", "satisfaction"]
    list_filter = ["statut"]
    search_fields = ["reference"]
