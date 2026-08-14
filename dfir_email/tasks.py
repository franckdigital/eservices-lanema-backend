import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def sync_tous_comptes_email_dfir():
    """Synchronise (IMAP) tous les comptes email DFIR actifs. Planifiée dans
    ediligence/celery.py (beat_schedule). Ne fait rien si Celery/worker+beat
    ne tournent pas — le bouton "Synchroniser" côté frontend fonctionne alors
    en synchrone, indépendamment de cette tâche planifiée."""
    from .models import CompteEmailDFIR
    from .services import sync_compte

    comptes = CompteEmailDFIR.objects.exclude(statut="INACTIF").exclude(serveur_entrant="")
    total = 0
    for compte in comptes:
        try:
            total += sync_compte(compte)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Échec synchro compte email DFIR #%s : %s", compte.pk, exc)
            compte.statut = "ERREUR"
            compte.derniere_erreur = str(exc)
            compte.save(update_fields=["statut", "derniere_erreur"])
    return total
