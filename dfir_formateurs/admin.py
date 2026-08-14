from django.contrib import admin

from .models import FormateurDFIR


@admin.register(FormateurDFIR)
class FormateurDFIRAdmin(admin.ModelAdmin):
    list_display = ["user", "specialite", "date_qualification", "disponible"]
    list_filter = ["disponible"]
