from django.contrib import admin

from .models import (
    CollaborationRecherche,
    ProjetRecherche,
    PublicationScientifique,
    RapportRecherche,
    RecommandationRecherche,
)


@admin.register(ProjetRecherche)
class ProjetRechercheAdmin(admin.ModelAdmin):
    list_display = ["reference", "titre", "type_projet", "statut", "date_debut"]
    list_filter = ["type_projet", "statut"]
    search_fields = ["reference", "titre"]


@admin.register(PublicationScientifique)
class PublicationScientifiqueAdmin(admin.ModelAdmin):
    list_display = ["titre", "projet", "date_publication"]


@admin.register(RapportRecherche)
class RapportRechercheAdmin(admin.ModelAdmin):
    list_display = ["titre", "projet", "valide", "date_creation"]
    list_filter = ["valide"]


@admin.register(RecommandationRecherche)
class RecommandationRechercheAdmin(admin.ModelAdmin):
    list_display = ["rapport", "appliquee"]
    list_filter = ["appliquee"]


@admin.register(CollaborationRecherche)
class CollaborationRechercheAdmin(admin.ModelAdmin):
    list_display = ["nom_partenaire", "type_partenaire", "date_debut"]
    list_filter = ["type_partenaire"]
