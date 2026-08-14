from django.contrib import admin

from .models import Budget, Depense, EcritureComptable, Recette


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["annee", "categorie", "direction", "montant_prevu", "montant_engage", "montant_realise"]
    list_filter = ["annee", "categorie"]


@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ["reference", "date_ecriture", "type", "montant", "erreur"]
    list_filter = ["type", "erreur"]


@admin.register(Recette)
class RecetteAdmin(admin.ModelAdmin):
    list_display = ["reference", "direction", "client_nom", "montant", "statut", "date_emission"]
    list_filter = ["statut"]


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ["reference", "direction", "categorie", "montant", "statut", "date_engagement"]
    list_filter = ["categorie", "statut"]
