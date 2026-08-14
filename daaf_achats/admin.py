from django.contrib import admin

from .models import BonCommande, DemandeAchat, Fournisseur, Marche


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ["nom", "contact", "actif"]
    list_filter = ["actif"]


@admin.register(DemandeAchat)
class DemandeAchatAdmin(admin.ModelAdmin):
    list_display = ["reference", "objet", "direction", "statut", "date_demande"]
    list_filter = ["statut"]


@admin.register(BonCommande)
class BonCommandeAdmin(admin.ModelAdmin):
    list_display = ["reference", "fournisseur_nom", "montant", "statut", "date_livraison_prevue", "conforme"]
    list_filter = ["statut", "conforme"]


@admin.register(Marche)
class MarcheAdmin(admin.ModelAdmin):
    list_display = ["reference", "objet", "montant", "statut", "respect_plan"]
    list_filter = ["statut", "respect_plan"]
