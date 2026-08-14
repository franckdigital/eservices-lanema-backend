from django.contrib import admin

from .models import FactureFournisseur, FournisseurComptable, PaiementFournisseur


@admin.register(FournisseurComptable)
class FournisseurComptableAdmin(admin.ModelAdmin):
    list_display = ["raison_sociale", "contact_nom", "telephone", "actif"]
    list_filter = ["actif"]
    search_fields = ["raison_sociale", "rccm"]


@admin.register(FactureFournisseur)
class FactureFournisseurAdmin(admin.ModelAdmin):
    list_display = ["reference", "fournisseur", "montant_ttc", "statut", "date_reception", "date_echeance"]
    list_filter = ["statut"]
    search_fields = ["reference"]


@admin.register(PaiementFournisseur)
class PaiementFournisseurAdmin(admin.ModelAdmin):
    list_display = ["facture_fournisseur", "montant", "mode_paiement", "date_paiement"]
    list_filter = ["mode_paiement"]
