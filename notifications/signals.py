"""
Signals pour générer des notifications automatiques sur les actions clés
Notifie à la fois les admins et les clients concernés
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import creer_notification, notifier_admins, notifier_utilisateurs_par_role


# ============================================
# STOCK SIGNALS
# ============================================

@receiver(post_save, sender='stock.Quarantaine')
def notification_quarantaine(sender, instance, created, **kwargs):
    """Notification quand un lot est mis en quarantaine ou levé"""
    if created:
        notifier_admins(
            titre=f"Lot mis en quarantaine",
            message=f"Le lot {instance.lot.numero_lot} a été mis en quarantaine. Motif: {instance.motif}",
            type_notification="STOCK",
            priorite="HAUTE",
            lien="/app/stock/quarantaines"
        )
    elif instance.levee:
        notifier_admins(
            titre=f"Quarantaine levée",
            message=f"La quarantaine du lot {instance.lot.numero_lot} a été levée. Décision: {instance.decision}",
            type_notification="STOCK",
            priorite="NORMALE",
            lien="/app/stock/quarantaines"
        )


@receiver(post_save, sender='stock.Alerte')
def notification_alerte_stock(sender, instance, created, **kwargs):
    """Notification pour les alertes de stock"""
    if created:
        notifier_admins(
            titre=f"Alerte stock: {instance.type_alerte}",
            message=instance.message,
            type_notification="ALERTE",
            priorite="HAUTE" if instance.type_alerte in ["RUPTURE", "PEREMPTION"] else "NORMALE",
            lien="/app/stock/alertes"
        )


@receiver(post_save, sender='stock.Reception')
def notification_reception(sender, instance, created, **kwargs):
    """Notification quand une réception est créée"""
    if created:
        notifier_admins(
            titre=f"Nouvelle réception: {instance.numero_reception}",
            message=f"Fournisseur: {instance.fournisseur}",
            type_notification="STOCK",
            priorite="NORMALE",
            lien="/app/stock/receptions"
        )


@receiver(post_save, sender='stock.SortieStock')
def notification_sortie_stock(sender, instance, created, **kwargs):
    """Notification quand une sortie de stock est effectuée"""
    if created:
        notifier_admins(
            titre=f"Sortie de stock: {instance.numero_sortie}",
            message=f"Motif: {instance.motif}",
            type_notification="STOCK",
            priorite="NORMALE",
            lien="/app/stock/sorties"
        )


# ============================================
# DEMANDES SIGNALS - Notifications client + admin
# ============================================

@receiver(post_save, sender='demandes.DemandeDevis')
def notification_demande(sender, instance, created, **kwargs):
    """Notification pour les demandes de devis - notifie client ET admin"""
    if created:
        # Notifier les admins d'une nouvelle demande
        notifier_admins(
            titre=f"Nouvelle demande d'analyse: {instance.numero}",
            message=f"Type: {instance.type_analyse}. Client: {instance.client.email if instance.client else 'N/A'}",
            type_notification="DEMANDE",
            priorite="HAUTE",
            lien="/app/clients"
        )
        # Confirmer au client que sa demande a été reçue
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Demande reçue: {instance.numero}",
                message=f"Votre demande d'analyse {instance.type_analyse} a bien été enregistrée. Nous la traiterons dans les plus brefs délais.",
                type_notification="DEMANDE",
                priorite="NORMALE",
                lien="/devis/demandes"
            )
    else:
        # Changements de statut - notifier le client (statuts réels: EN_ATTENTE, EN_COURS, ACCEPTEE, REFUSEE)
        old_statut = getattr(instance, "_old_statut", None)

        if old_statut == instance.statut:
            return

        if instance.client:
            statut_messages = {
                "EN_ATTENTE": ("Demande en attente", "Votre demande est en attente de traitement.", "NORMALE"),
                "EN_COURS": ("Demande en cours de traitement", "Votre demande d'analyse est en cours de traitement par notre équipe.", "NORMALE"),
                "ACCEPTEE": ("Demande acceptée", "Votre demande d'analyse a été acceptée. Les travaux vont commencer.", "HAUTE"),
                "REFUSEE": ("Demande refusée", "Nous sommes désolés, votre demande n'a pas pu être acceptée.", "NORMALE"),
            }
            if instance.statut in statut_messages:
                titre, message, priorite = statut_messages[instance.statut]
                creer_notification(
                    user=instance.client,
                    titre=f"{titre}: {instance.numero}",
                    message=message,
                    type_notification="DEMANDE",
                    priorite=priorite,
                    lien="/devis/demandes"
                )

        # Notifier aussi les admins des changements importants
        if instance.statut in ["ACCEPTEE", "REFUSEE"]:
            notifier_admins(
                titre=f"Demande {instance.statut.lower()}: {instance.numero}",
                message=f"La demande {instance.numero} du client {instance.client.email} est maintenant {instance.statut.lower()}.",
                type_notification="DEMANDE",
                priorite="NORMALE",
                lien="/app/clients"
            )


@receiver(pre_save, sender='demandes.DemandeDevis')
def capture_old_statut_demande(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_statut = None
        return
    try:
        instance._old_statut = sender.objects.get(pk=instance.pk).statut
    except sender.DoesNotExist:
        instance._old_statut = None


# ============================================
# QUALITÉ SIGNALS
# ============================================

@receiver(post_save, sender='qualite.NonConformite')
def notification_non_conformite(sender, instance, created, **kwargs):
    """Notification pour les non-conformités"""
    if created:
        priorite = "URGENTE" if instance.gravite == "CRITIQUE" else "HAUTE" if instance.gravite == "MAJEURE" else "NORMALE"
        notifier_admins(
            titre=f"Nouvelle non-conformité: {instance.numero}",
            message=f"Gravité: {instance.gravite}. {instance.description[:100]}..." if len(instance.description) > 100 else f"Gravité: {instance.gravite}. {instance.description}",
            type_notification="QUALITE",
            priorite=priorite,
            lien="/app/qualite"
        )


@receiver(post_save, sender='qualite.Echantillon')
def notification_echantillon(sender, instance, created, **kwargs):
    """Notification pour les échantillons"""
    if created:
        notifier_admins(
            titre=f"Nouvel échantillon: {instance.code_echantillon}",
            message=f"Désignation: {instance.designation}",
            type_notification="ECHANTILLON",
            priorite="NORMALE",
            lien="/app/echantillons"
        )
        # Notifier le client si lié à une demande
        if instance.demande and instance.demande.client:
            creer_notification(
                user=instance.demande.client,
                titre=f"Échantillon enregistré: {instance.code_echantillon}",
                message=f"Votre échantillon '{instance.designation}' a été enregistré et est prêt pour analyse.",
                type_notification="ECHANTILLON",
                priorite="NORMALE",
                lien="/devis/demandes"
            )


@receiver(post_save, sender='qualite.Essai')
def notification_essai(sender, instance, created, **kwargs):
    """Notification pour les essais"""
    if created:
        notifier_admins(
            titre=f"Nouvel essai: {instance.numero}",
            message=f"Type: {instance.type_essai}",
            type_notification="ESSAI",
            priorite="NORMALE",
            lien="/app/essais"
        )
    elif instance.statut == "TERMINE":
        notifier_admins(
            titre=f"Essai terminé: {instance.numero}",
            message=f"L'essai {instance.numero} est terminé et en attente de validation.",
            type_notification="ESSAI",
            priorite="HAUTE",
            lien="/app/essais"
        )
        # Notifier le client si lié à un échantillon avec demande
        if hasattr(instance, 'echantillon') and instance.echantillon:
            echantillon = instance.echantillon
            if hasattr(echantillon, 'demande') and echantillon.demande and echantillon.demande.client:
                creer_notification(
                    user=echantillon.demande.client,
                    titre=f"Essai terminé: {instance.numero}",
                    message=f"L'essai sur votre échantillon est terminé. Les résultats seront bientôt disponibles.",
                    type_notification="ESSAI",
                    priorite="HAUTE",
                    lien="/devis/demandes"
                )


# ============================================
# FACTURATION SIGNALS - Notifications client + admin
# ============================================

@receiver(post_save, sender='facturation.Facture')
def notification_facture(sender, instance, created, **kwargs):
    """Notification pour les factures - notifie client ET admin"""
    if created:
        # Notifier le client
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Nouvelle facture: {instance.numero}",
                message=f"Une nouvelle facture de {instance.montant_ttc} {instance.devise} a été émise.",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/devis/factures"
            )
        # Notifier les admins
        notifier_admins(
            titre=f"Facture créée: {instance.numero}",
            message=f"Facture de {instance.montant_ttc} {instance.devise} pour {instance.client.email if instance.client else 'N/A'}",
            type_notification="FACTURATION",
            priorite="NORMALE",
            lien="/app/facturation"
        )
    else:
        old_statut = getattr(instance, "_old_statut", None)

        if old_statut == instance.statut:
            return

        # Changements de statut
        if instance.client:
            statut_messages = {
                "ENVOYEE": ("Facture envoyée", "Votre facture a été envoyée. Veuillez procéder au paiement.", "HAUTE"),
                "EN_ATTENTE_VALIDATION": (
                    "Paiement soumis",
                    "Votre preuve de paiement a été transmise et est en attente de validation.",
                    "HAUTE",
                ),
                "PAYEE": ("Paiement validé", "Votre paiement a été validé. Merci!", "HAUTE"),
                "ANNULEE": ("Facture annulée", "Votre facture a été annulée.", "NORMALE"),
                "EN_RETARD": ("Facture en retard", "Votre facture est en retard de paiement. Veuillez régulariser.", "URGENTE"),
            }
            if instance.statut in statut_messages:
                titre, message, priorite = statut_messages[instance.statut]
                creer_notification(
                    user=instance.client,
                    titre=f"{titre}: {instance.numero}",
                    message=message,
                    type_notification="FACTURATION",
                    priorite=priorite,
                    lien="/devis/factures"
                )

        # Notifier admin quand une preuve est soumise
        if instance.statut == "EN_ATTENTE_VALIDATION":
            notifier_admins(
                titre=f"Preuve de paiement soumise: {instance.numero}",
                message=f"Le client {instance.client.email if instance.client else 'N/A'} a soumis une preuve de paiement. Montant: {instance.montant_ttc} {instance.devise}",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/app/facturation"
            )

        # Notifier admin pour paiement validé
        if instance.statut == "PAYEE":
            notifier_admins(
                titre=f"Paiement validé: {instance.numero}",
                message=f"Facture {instance.numero} payée. Montant: {instance.montant_ttc} {instance.devise}",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/app/facturation"
            )


@receiver(pre_save, sender='facturation.Facture')
def capture_old_statut_facture(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_statut = None
        return
    try:
        instance._old_statut = sender.objects.get(pk=instance.pk).statut
    except sender.DoesNotExist:
        instance._old_statut = None


@receiver(post_save, sender='facturation.Proforma')
def notification_proforma(sender, instance, created, **kwargs):
    """Notification pour les proformas - notifie client ET admin"""
    if created:
        # Notifier le client
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Nouveau devis: {instance.numero}",
                message=f"Un devis de {instance.montant_ttc} {instance.devise} a été créé pour vous.",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/devis/factures"
            )
        # Notifier les admins
        notifier_admins(
            titre=f"Proforma créée: {instance.numero}",
            message=f"Proforma de {instance.montant_ttc} {instance.devise} pour {instance.client.email if instance.client else 'N/A'}",
            type_notification="FACTURATION",
            priorite="NORMALE",
            lien="/app/facturation"
        )
    else:
        old_statut = getattr(instance, "_old_statut", None)

        if old_statut == instance.statut:
            return

        if instance.client:
            # statuts réels: BROUILLON, ENVOYEE, VALIDEE, ACCEPTEE, REFUSEE, ANNULEE
            statut_messages = {
                "VALIDEE": ("Devis validé", "Votre devis a été validé. Une facture va être générée.", "HAUTE"),
                "ACCEPTEE": ("Devis accepté", "Merci d'avoir accepté notre devis. Le traitement va commencer.", "HAUTE"),
                "REFUSEE": ("Devis refusé", "Votre devis a été marqué comme refusé.", "NORMALE"),
                "ANNULEE": ("Devis annulé", "Votre devis a été annulé.", "NORMALE"),
            }
            if instance.statut in statut_messages:
                titre, message, priorite = statut_messages[instance.statut]
                creer_notification(
                    user=instance.client,
                    titre=f"{titre}: {instance.numero}",
                    message=message,
                    type_notification="FACTURATION",
                    priorite=priorite,
                    lien="/devis/factures"
                )

        # Notifier admin si proforma acceptée / validée
        if instance.statut in ["ACCEPTEE", "VALIDEE"]:
            notifier_admins(
                titre=f"Proforma {instance.statut.lower()}: {instance.numero}",
                message=f"La proforma {instance.numero} du client {instance.client.email if instance.client else 'N/A'} a été {instance.statut.lower()}.",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/app/facturation"
            )


@receiver(pre_save, sender='facturation.Proforma')
def capture_old_statut_proforma(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_statut = None
        return
    try:
        instance._old_statut = sender.objects.get(pk=instance.pk).statut
    except sender.DoesNotExist:
        instance._old_statut = None


@receiver(post_save, sender='facturation.BonCommande')
def notification_bon_commande(sender, instance, created, **kwargs):
    """Notifications sur le bon de commande - le client doit le signer avant
    de pouvoir payer sa facture (cf. FactureViewSet.payer)."""
    if created:
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Bon de commande à signer: {instance.numero}",
                message="Un bon de commande a été émis pour votre devis accepté. Merci de le signer électroniquement avant de procéder au paiement de la facture.",
                type_notification="FACTURATION",
                priorite="HAUTE",
                lien="/devis/bons-commande"
            )
        notifier_admins(
            titre=f"Bon de commande émis: {instance.numero}",
            message=f"Bon de commande de {instance.montant_ttc} {instance.devise} pour {instance.client.email if instance.client else 'N/A'}",
            type_notification="FACTURATION",
            priorite="NORMALE",
            lien="/app/facturation"
        )
        return

    old_statut = getattr(instance, "_old_statut", None)
    if old_statut == instance.statut:
        return

    if instance.statut == "SIGNE_CLIENT":
        notifier_admins(
            titre=f"Bon de commande signé: {instance.numero}",
            message=f"Le client {instance.client.email if instance.client else 'N/A'} a signé le bon de commande {instance.numero}. Le paiement de la facture peut être engagé.",
            type_notification="FACTURATION",
            priorite="HAUTE",
            lien="/app/facturation"
        )
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Bon de commande signé: {instance.numero}",
                message="Votre bon de commande a bien été signé. Vous pouvez désormais procéder au paiement de votre facture.",
                type_notification="FACTURATION",
                priorite="NORMALE",
                lien="/devis/factures"
            )


@receiver(pre_save, sender='facturation.BonCommande')
def capture_old_statut_bon_commande(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_statut = None
        return
    try:
        instance._old_statut = sender.objects.get(pk=instance.pk).statut
    except sender.DoesNotExist:
        instance._old_statut = None


@receiver(post_save, sender='facturation.DemandeAnalyse')
def notification_demande_analyse(sender, instance, created, **kwargs):
    """Notifications sur les demandes d'analyse (confirmation admin, analyse démarrée, etc.)"""
    if created:
        # DemandeAnalyse créée automatiquement après acceptation de devis
        if instance.client:
            creer_notification(
                user=instance.client,
                titre=f"Demande d'analyse créée: {instance.numero}",
                message="Votre demande d'analyse a été créée. Nous attendons vos échantillons pour démarrer.",
                type_notification="DEMANDE",
                priorite="HAUTE",
                lien="/devis/demandes"
            )
        notifier_admins(
            titre=f"Demande d'analyse créée: {instance.numero}",
            message=f"Demande d'analyse pour {instance.client.email if instance.client else 'N/A'}.",
            type_notification="DEMANDE",
            priorite="NORMALE",
            lien="/app/demandes"
        )
        return

    old_statut = getattr(instance, "_old_statut", None)

    if old_statut == instance.statut:
        return

    # statuts réels: EN_ATTENTE_ECHANTILLONS, ECHANTILLONS_RECUS, EN_COURS, TERMINEE, RESULTATS_ENVOYES
    if instance.client:
        statut_messages = {
            "ECHANTILLONS_RECUS": (
                "Échantillons reçus",
                "Nous avons bien reçu vos échantillons. L'analyse va démarrer.",
                "HAUTE",
            ),
            "EN_COURS": (
                "Analyse démarrée",
                "Votre analyse est en cours. Nous vous tiendrons informé de l'avancement.",
                "HAUTE",
            ),
            "TERMINEE": (
                "Analyse terminée",
                "Votre analyse est terminée. Les résultats seront disponibles.",
                "HAUTE",
            ),
            "RESULTATS_ENVOYES": (
                "Résultats envoyés",
                "Les résultats de votre analyse ont été envoyés.",
                "HAUTE",
            ),
        }
        if instance.statut in statut_messages:
            titre, message, priorite = statut_messages[instance.statut]
            creer_notification(
                user=instance.client,
                titre=f"{titre}: {instance.numero}",
                message=message,
                type_notification="DEMANDE",
                priorite=priorite,
                lien="/devis/demandes"
            )

    # Notifier admins sur démarrage/fin
    if instance.statut in ["EN_COURS", "TERMINEE", "RESULTATS_ENVOYES"]:
        notifier_admins(
            titre=f"Demande d'analyse {instance.statut.lower()}: {instance.numero}",
            message=f"Demande {instance.numero} ({instance.client.email if instance.client else 'N/A'}) est maintenant {instance.statut.lower()}.",
            type_notification="DEMANDE",
            priorite="NORMALE",
            lien="/app/demandes"
        )


@receiver(pre_save, sender='facturation.DemandeAnalyse')
def capture_old_statut_demande_analyse(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_statut = None
        return
    try:
        instance._old_statut = sender.objects.get(pk=instance.pk).statut
    except sender.DoesNotExist:
        instance._old_statut = None


# ============================================
# MÉTROLOGIE SIGNALS
# ============================================

@receiver(post_save, sender='metrologie.Equipement')
def notification_equipement(sender, instance, created, **kwargs):
    """Notification pour les équipements"""
    if instance.statut == "ETALONNAGE_REQUIS":
        notifier_admins(
            titre=f"Étalonnage requis: {instance.code}",
            message=f"L'équipement {instance.designation} nécessite un étalonnage.",
            type_notification="METROLOGIE",
            priorite="HAUTE",
            lien="/app/metrologie"
        )
    elif instance.statut == "HORS_SERVICE":
        notifier_admins(
            titre=f"Équipement hors service: {instance.code}",
            message=f"L'équipement {instance.designation} est hors service.",
            type_notification="METROLOGIE",
            priorite="URGENTE",
            lien="/app/metrologie"
        )


@receiver(post_save, sender='metrologie.Etalonnage')
def notification_etalonnage(sender, instance, created, **kwargs):
    """Notification pour les étalonnages"""
    if created:
        notifier_admins(
            titre=f"Nouvel étalonnage: {instance.equipement.code if instance.equipement else 'N/A'}",
            message=f"Un étalonnage a été planifié pour l'équipement {instance.equipement.designation if instance.equipement else 'N/A'}.",
            type_notification="METROLOGIE",
            priorite="NORMALE",
            lien="/app/metrologie"
        )
    elif hasattr(instance, 'statut') and instance.statut == "TERMINE":
        notifier_admins(
            titre=f"Étalonnage terminé",
            message=f"L'étalonnage de {instance.equipement.code if instance.equipement else 'N/A'} est terminé.",
            type_notification="METROLOGIE",
            priorite="NORMALE",
            lien="/app/metrologie"
        )
