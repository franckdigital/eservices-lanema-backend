from django.contrib import admin
from .models import Facture, Proforma, DemandeAnalyse


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "client",
        "montant_ttc",
        "statut",
        "date_emission",
        "date_echeance",
        "visible_client",
        "paiement_valide",
    ]
    list_filter = ["statut", "visible_client", "paiement_valide", "date_emission"]
    search_fields = ["numero", "client__email", "client__first_name", "client__last_name"]
    list_editable = ["visible_client", "statut"]
    readonly_fields = ["numero", "date_emission", "date_paiement"]
    
    fieldsets = (
        ("Informations générales", {
            "fields": ("numero", "client", "date_emission", "date_echeance")
        }),
        ("Montants", {
            "fields": ("montant_ht", "montant_ttc", "devise")
        }),
        ("Statut et visibilité", {
            "fields": ("statut", "visible_client")
        }),
        ("Paiement", {
            "fields": (
                "mode_paiement",
                "justificatif_paiement",
                "reference_paiement",
                "paiement_valide",
                "date_paiement",
            )
        }),
    )


@admin.register(Proforma)
class ProformaAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "client",
        "montant_ttc",
        "statut",
        "date_emission",
    ]
    list_filter = ["statut", "date_emission"]
    search_fields = ["numero", "client__email", "client__first_name", "client__last_name"]
    readonly_fields = ["numero", "date_emission"]


@admin.register(DemandeAnalyse)
class DemandeAnalyseAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "client",
        "statut",
        "date_creation",
    ]
    list_filter = ["statut", "date_creation"]
    search_fields = ["numero", "client__email", "client__first_name", "client__last_name"]
    readonly_fields = ["numero", "date_creation"]
