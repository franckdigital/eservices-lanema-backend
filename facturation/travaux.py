"""Autorisation de demarrage des travaux : le service facturation (caisse /
comptabilite) valide le reglement du client — par cheque, bon de commande ou
especes — ce qui autorise les travaux et informe le service reception, le
laboratoire (analyses) ou la DMCT (metrologie).

Le laboratoire et la reception ne manipulent jamais l'argent : ils ne voient que
le resultat (« travaux autorises »)."""
from django.contrib.auth.models import User
from django.utils import timezone

TYPES_METROLOGIE = ("METROLOGIE", "ETALONNAGE_INSTRUMENTS", "ETALONNAGE_VERRERIE")
MODE_LIBELLES = {"CHEQUE": "chèque", "COMPTANT": "espèces", "BON_COMMANDE": "bon de commande du client"}
MESSAGE_BLOQUE = (
    "Les travaux ne peuvent démarrer qu'après le règlement du client (chèque, bon de commande ou espèces) "
    "validé par le service facturation."
)


def peut_demarrer(demande_devis):
    """Vrai si le reglement du devis a ete valide par la facturation."""
    from .models import Facture

    if demande_devis is None:
        return False
    return Facture.objects.filter(proforma__demande_devis=demande_devis, travaux_autorises=True).exists()


def _utilisateurs_dmct():
    from core.direction_access import DIRECTION_CODE_MAP

    nom = next((n for n, code in DIRECTION_CODE_MAP.items() if code == "DMCT"), None)
    if not nom:
        return []
    return list(User.objects.filter(profile__direction__nom=nom, is_active=True))


def _notifier(facture):
    demande = facture.proforma.demande_devis if facture.proforma else None
    metrologie = bool(demande and demande.type_analyse in TYPES_METROLOGIE)
    profil = getattr(facture.client, "client_profile", None)
    client = getattr(profil, "raison_sociale", "") or facture.client.get_full_name() or facture.client.username
    mode = MODE_LIBELLES.get(facture.mode_paiement, facture.mode_paiement or "règlement")
    titre = f"Règlement validé — dossier {demande.numero if demande else facture.numero}"
    message = (
        f"Facture {facture.numero} ({client}) : {mode} validé par le service facturation. "
        + ("L'équipement peut être réceptionné puis transmis à la DMCT." if metrologie else "Les échantillons peuvent être réceptionnés puis transmis au laboratoire.")
    )
    try:
        from notifications.models import creer_notification, notifier_utilisateurs_par_role

        notifier_utilisateurs_par_role("RECEPTION", titre, message, lien="/app/reception")
        if metrologie:
            for u in _utilisateurs_dmct():
                creer_notification(u, titre, message + " Fiche à réceptionner dans « Fiches d'exécution & certificats ».", lien="/dmct/travaux")
        else:
            for role in ("TECHNICIEN", "GESTIONNAIRE"):
                notifier_utilisateurs_par_role(role, titre, message, lien="/app/essais/fiches")
    except Exception:  # pragma: no cover - une notification ne bloque jamais l'encaissement
        pass
    if metrologie:  # notification e-diligence pour les agents DMCT
        try:
            from core.models import Notification as NotifEdiligence

            for u in _utilisateurs_dmct():
                NotifEdiligence.objects.create(user=u, type_notif="nouvelle_demande", contenu=message, message=message, lien="/dmct/travaux")
        except Exception:  # pragma: no cover
            pass


def autoriser_travaux(facture, user):
    """Autorise le demarrage des travaux (idempotent), cree la demande d'analyse
    et previent reception / laboratoire / DMCT."""
    from .views import _creer_demande_analyse_si_absente

    deja = facture.travaux_autorises
    if not deja:
        facture.travaux_autorises = True
        facture.travaux_autorises_le = timezone.now()
        facture.travaux_autorises_par = user
        facture.save(update_fields=["travaux_autorises", "travaux_autorises_le", "travaux_autorises_par"])
    _creer_demande_analyse_si_absente(facture)
    if not deja:
        _notifier(facture)
    return facture
