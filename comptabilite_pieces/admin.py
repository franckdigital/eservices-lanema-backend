from django.contrib import admin

from .models import PieceComptable


@admin.register(PieceComptable)
class PieceComptableAdmin(admin.ModelAdmin):
    list_display = ["numero", "type_piece", "source_reference", "montant", "statut", "date_piece"]
    list_filter = ["type_piece", "statut"]
    search_fields = ["numero", "source_reference"]
