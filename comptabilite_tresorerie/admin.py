from django.contrib import admin

from .models import CompteBancaire, MouvementBancaire, RapprochementBancaire


@admin.register(CompteBancaire)
class CompteBancaireAdmin(admin.ModelAdmin):
    list_display = ["nom_banque", "numero_compte", "solde_initial", "actif"]
    list_filter = ["actif"]
    search_fields = ["nom_banque", "numero_compte"]


@admin.register(MouvementBancaire)
class MouvementBancaireAdmin(admin.ModelAdmin):
    list_display = ["compte", "type_mouvement", "montant", "date_mouvement", "rapproche"]
    list_filter = ["type_mouvement", "rapproche"]


@admin.register(RapprochementBancaire)
class RapprochementBancaireAdmin(admin.ModelAdmin):
    list_display = ["compte", "date_rapprochement", "solde_releve", "solde_comptable", "ecart", "valide"]
    list_filter = ["valide"]
