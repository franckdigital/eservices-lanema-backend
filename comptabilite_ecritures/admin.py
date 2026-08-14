from django.contrib import admin

from .models import CompteComptable, EcritureComptable, JournalComptable


@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display = ["numero", "intitule", "type_compte"]
    list_filter = ["type_compte"]
    search_fields = ["numero", "intitule"]


@admin.register(JournalComptable)
class JournalComptableAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle"]


@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ["numero", "journal", "compte_debit", "compte_credit", "montant", "valide", "date_ecriture"]
    list_filter = ["journal", "valide"]
    search_fields = ["numero"]
