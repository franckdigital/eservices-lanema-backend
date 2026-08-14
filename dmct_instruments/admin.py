from django.contrib import admin

from .models import CertificatDMCT, InstrumentMesure


@admin.register(InstrumentMesure)
class InstrumentMesureAdmin(admin.ModelAdmin):
    list_display = ["reference", "designation", "type_instrument", "client", "statut"]
    list_filter = ["statut"]
    search_fields = ["reference", "designation"]


@admin.register(CertificatDMCT)
class CertificatDMCTAdmin(admin.ModelAdmin):
    list_display = ["numero", "instrument", "date_emission", "date_expiration"]
