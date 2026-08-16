"""Alertes DAE basees sur le temps (pas declenchables par un signal
post_save) — a executer periodiquement via cron sur le serveur, ex:
    0 8 * * * cd /var/www/... && venv/bin/python manage.py check_dae_alertes

Cf. cahier des charges DAE section 25 — 8 types d'alertes :
🔴 OT en retard · 🟠 OT proche de l'échéance · 🔴 Équipement immobilisé
trop longtemps · 🔴 Pièce critique en rupture · 🟠 Batterie arrivant à
échéance de contrôle · 🟠 Maintenance préventive à réaliser ·
🔴 Non-conformité critique · 🔴 Action corrective en retard.

Une seule notification par element signale et par jour (evite le spam a
chaque execution du cron) — verifie via un doublon exact (user, type_notif,
contenu, created_at__date)."""
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

SEUIL_ECHEANCE_PROCHE_JOURS = 2
SEUIL_IMMOBILISATION_JOURS = 30
SEUIL_MAINTENANCE_PREVENTIVE_JOURS = 3


class Command(BaseCommand):
    help = "Génère les 8 types d'alertes automatiques de la DAE (cf. cahier des charges section 25)"

    def handle(self, *args, **options):
        from django.contrib.auth.models import User

        from core.models import Notification

        today = timezone.now().date()
        destinataires = list(User.objects.filter(
            profile__direction__nom="Direction de l'Aéronautique",
            profile__role__in=["ADMIN", "DIRECTEUR", "SOUS_DIRECTEUR", "CHEF_SERVICE"],
        ))
        if not destinataires:
            self.stdout.write("Aucun destinataire DAE (Admin/Directeur/Sous-directeur/Chef de service) trouvé.")
            return

        total = 0
        total += self._alertes_ot(today, destinataires, Notification)
        total += self._alertes_equipements(today, destinataires, Notification)
        total += self._alertes_pieces(destinataires, Notification)
        total += self._alertes_batteries(today, destinataires, Notification)
        total += self._alertes_maintenance_preventive(today, destinataires, Notification)
        total += self._alertes_non_conformites(destinataires, Notification)
        total += self._alertes_actions_correctives(today, destinataires, Notification)

        self.stdout.write(self.style.SUCCESS(f"{total} alerte(s) DAE signalée(s)."))

    def _notifier(self, destinataires, contenu, lien, today, Notification):
        for user in destinataires:
            already_sent_today = Notification.objects.filter(
                user=user, type_notif="rappel", contenu=contenu, created_at__date=today,
            ).exists()
            if not already_sent_today:
                Notification.objects.create(user=user, type_notif="rappel", contenu=contenu, lien=lien)

    def _alertes_ot(self, today, destinataires, Notification):
        """🔴 OT en retard + 🟠 OT proche de l'échéance."""
        from aero_maintenance.models import OrdreTravail

        actifs = OrdreTravail.objects.filter(date_fin_prevue__isnull=False).exclude(
            statut__in=["TERMINE", "VALIDE", "CLOTURE", "ANNULE"]
        ).select_related("aeronef")

        count = 0
        for ot in actifs:
            if ot.date_fin_prevue < today:
                jours_retard = (today - ot.date_fin_prevue).days
                contenu = (
                    f"🔴 Ordre de travail en retard de {jours_retard} jour(s) : {ot.reference} "
                    f"({ot.aeronef.immatriculation if ot.aeronef else '—'})"
                )
                self._notifier(destinataires, contenu, "/dae/maintenance", today, Notification)
                count += 1
            elif (ot.date_fin_prevue - today).days <= SEUIL_ECHEANCE_PROCHE_JOURS:
                contenu = (
                    f"🟠 Ordre de travail proche de l'échéance ({ot.date_fin_prevue}) : {ot.reference} "
                    f"({ot.aeronef.immatriculation if ot.aeronef else '—'})"
                )
                self._notifier(destinataires, contenu, "/dae/maintenance", today, Notification)
                count += 1
        return count

    def _alertes_equipements(self, today, destinataires, Notification):
        """🔴 Équipement immobilisé depuis trop longtemps."""
        from aero_maintenance.models import EquipementAeronautique

        seuil_date = today - timezone.timedelta(days=SEUIL_IMMOBILISATION_JOURS)
        immobilises = EquipementAeronautique.objects.exclude(statut="EN_SERVICE").filter(
            date_reception__lte=seuil_date
        )
        count = 0
        for eq in immobilises:
            jours = (today - eq.date_reception).days
            contenu = (
                f"🔴 Équipement immobilisé depuis {jours} jours : {eq.reference or eq.numero_serie} "
                f"({eq.get_statut_display()})"
            )
            self._notifier(destinataires, contenu, "/dae/maintenance", today, Notification)
            count += 1
        return count

    def _alertes_pieces(self, destinataires, Notification):
        """🔴 Pièce critique en rupture."""
        from aero_stock.models import PieceRechange

        today = timezone.now().date()
        rupture = PieceRechange.objects.filter(est_critique=True, quantite_stock__lte=F("seuil_alerte"))
        count = 0
        for piece in rupture:
            contenu = f"🔴 Pièce critique en rupture : {piece.designation} ({piece.quantite_stock} en stock, seuil {piece.seuil_alerte})"
            self._notifier(destinataires, contenu, "/dae/stock", today, Notification)
            count += 1
        return count

    def _alertes_batteries(self, today, destinataires, Notification):
        """🟠 Batterie arrivant à échéance de contrôle."""
        from aero_maintenance.models import BatterieAeronef

        seuil_date = today + timezone.timedelta(days=SEUIL_ECHEANCE_PROCHE_JOURS)
        batteries = BatterieAeronef.objects.filter(
            prochain_controle__isnull=False, prochain_controle__lte=seuil_date
        ).exclude(statut="HORS_SERVICE")
        count = 0
        for b in batteries:
            contenu = f"🟠 Batterie {b.reference or b.numero_serie} arrivant à échéance de contrôle ({b.prochain_controle})"
            self._notifier(destinataires, contenu, "/dae/maintenance", today, Notification)
            count += 1
        return count

    def _alertes_maintenance_preventive(self, today, destinataires, Notification):
        """🟠 Maintenance préventive à réaliser."""
        from aero_atelier.models import MaintenancePreventiveAtelier

        seuil_date = today + timezone.timedelta(days=SEUIL_MAINTENANCE_PREVENTIVE_JOURS)
        maintenances = MaintenancePreventiveAtelier.objects.filter(
            statut="PLANIFIEE", date_prevue__lte=seuil_date
        ).select_related("equipement")
        count = 0
        for m in maintenances:
            contenu = f"🟠 Maintenance préventive à réaliser : {m.equipement.designation} ({m.date_prevue})"
            self._notifier(destinataires, contenu, "/dae/atelier", today, Notification)
            count += 1
        return count

    def _alertes_non_conformites(self, destinataires, Notification):
        """🔴 Non-conformité critique."""
        from aero_qualite.models import NonConformiteDAE

        today = timezone.now().date()
        critiques = NonConformiteDAE.objects.filter(gravite="CRITIQUE").exclude(statut="CLOTUREE")
        count = 0
        for nc in critiques:
            contenu = f"🔴 Non-conformité critique ouverte : {nc.reference} — {nc.description[:80]}"
            self._notifier(destinataires, contenu, "/dae/qualite", today, Notification)
            count += 1
        return count

    def _alertes_actions_correctives(self, today, destinataires, Notification):
        """🔴 Action corrective en retard."""
        from aero_qualite.models import ActionCorrectiveDAE

        en_retard = ActionCorrectiveDAE.objects.filter(
            date_prevue__lt=today, statut__in=["PLANIFIEE", "EN_COURS"],
        ).select_related("non_conformite")
        count = 0
        for action in en_retard:
            jours_retard = (today - action.date_prevue).days
            contenu = (
                f"🔴 Action corrective en retard de {jours_retard} jour(s) : {action.non_conformite.reference} — "
                f"{action.description[:80]}"
            )
            self._notifier(destinataires, contenu, "/dae/qualite", today, Notification)
            count += 1
        return count
