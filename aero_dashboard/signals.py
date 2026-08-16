"""Notifications DAE — meme mecanisme que core/signals.py
(@receiver(post_save, ...) -> core.Notification.objects.create), cable dans
AeroDashboardConfig.ready(). Portee volontairement limitee aux evenements a
forte valeur metier (cf. plan Phase 3.2), pas une notification par modele."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def _notifier_encadrement_dae(type_notif, contenu, lien=""):
    from core.models import Notification

    destinataires = User.objects.filter(
        profile__direction__nom="Direction de l'Aéronautique",
        profile__role__in=["ADMIN", "DIRECTEUR", "SOUS_DIRECTEUR", "CHEF_SERVICE"],
    )
    for user in destinataires:
        Notification.objects.create(user=user, type_notif=type_notif, contenu=contenu, lien=lien)


@receiver(post_save, sender="aero_maintenance.OrdreTravail")
def notifier_ordre_travail_assigne(sender, instance, created, **kwargs):
    if not created or not instance.technicien_id:
        return
    from core.models import Notification

    Notification.objects.create(
        user=instance.technicien,
        type_notif="nouvelle_demande",
        contenu=f"Nouvel ordre de travail assigné : {instance.reference} ({instance.aeronef.immatriculation if instance.aeronef else ''})",
        lien="/dae/maintenance",
    )


@receiver(post_save, sender="aero_qualite.NonConformiteDAE")
def notifier_non_conformite_critique(sender, instance, created, **kwargs):
    if not created or instance.gravite != "CRITIQUE":
        return
    _notifier_encadrement_dae(
        "rappel",
        f"Non-conformité CRITIQUE enregistrée : {instance.reference}",
        lien="/dae/qualite",
    )


@receiver(post_save, sender="aero_stock.PieceRechange")
def notifier_rupture_stock(sender, instance, created, **kwargs):
    if instance.seuil_alerte <= 0 or instance.quantite_stock > instance.seuil_alerte:
        return
    _notifier_encadrement_dae(
        "rappel",
        f"Stock faible : {instance.designation} ({instance.quantite_stock} restant, seuil {instance.seuil_alerte})",
        lien="/dae/stock",
    )


@receiver(post_save, sender="aero_clients.DemandeDAE")
def notifier_nouvelle_demande(sender, instance, created, **kwargs):
    """Cf. cahier des charges DAE section 28 — declencheur "nouvelle demande"."""
    if not created:
        return
    _notifier_encadrement_dae(
        "nouvelle_demande",
        f"Nouvelle demande de prestation : {instance.reference} ({instance.client.nom})",
        lien="/dae/clients",
    )


@receiver(post_save, sender="aero_clients.ReclamationClientDAE")
def notifier_nouvelle_reclamation(sender, instance, created, **kwargs):
    """Cf. cahier des charges DAE section 28 — declencheur "réclamation"."""
    if not created:
        return
    _notifier_encadrement_dae(
        "rappel",
        f"Nouvelle réclamation : {instance.reference} ({instance.client.nom}) — {instance.get_type_reclamation_display()}",
        lien="/dae/clients",
    )
