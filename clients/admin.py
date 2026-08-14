from django.contrib import admin

from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "raison_sociale", "telephone", "type_subscription")
    list_filter = ("role", "type_subscription")
    search_fields = ("user__username", "user__email", "raison_sociale", "siret", "contact_nom")
