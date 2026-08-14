from django.contrib import admin

from .models import Laboratoire


@admin.register(Laboratoire)
class LaboratoireAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "responsable", "capacite_journaliere"]
