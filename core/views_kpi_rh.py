"""KPI decisionnels RH pour le tableau de bord DAAF.

Fichier separe (comme views_kpi_ged.py) pour ne pas alourdir davantage
views.py/views_rh.py. Calculs autonomes, independants de ceux de
views_executive_kpi.py (pas d'import croise, pour eviter tout couplage
fragile avec ce fichier deja tres volumineux)."""
import datetime

from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Diligence, DemandeConge, FicheAgent, InscriptionFormationRH, Presence

HEURE_LIMITE_PONCTUALITE = datetime.time(8, 30)


def _business_days(date_debut, date_fin):
    jours = 0
    current = date_debut
    while current <= date_fin:
        if current.weekday() < 5:
            jours += 1
        current += datetime.timedelta(days=1)
    return jours


def compute_rh_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI Ressources Humaines. Reutilisable directement par le
    tableau de bord DAAF."""
    today = timezone.now().date()
    if date_debut and date_fin:
        if isinstance(date_debut, str):
            date_debut = datetime.datetime.strptime(date_debut, "%Y-%m-%d").date()
        if isinstance(date_fin, str):
            date_fin = datetime.datetime.strptime(date_fin, "%Y-%m-%d").date()
        periode_debut, periode_fin = date_debut, date_fin
    else:
        periode_debut, periode_fin = today.replace(day=1), today

    effectif_total = FicheAgent.objects.filter(statut="actif").count()
    jours_ouvres = _business_days(periode_debut, periode_fin) or 1
    capacite_presences = effectif_total * jours_ouvres

    presences = Presence.objects.filter(date_presence__range=(periode_debut, periode_fin))
    nb_presents = presences.filter(statut="présent").count()
    nb_absents = presences.filter(statut="absent").count()
    taux_presence = round(nb_presents / capacite_presences * 100, 1) if capacite_presences else None
    taux_absenteisme = round(nb_absents / capacite_presences * 100, 1) if capacite_presences else None

    presences_avec_arrivee = presences.filter(heure_arrivee__isnull=False)
    nb_retards = presences_avec_arrivee.filter(heure_arrivee__gt=HEURE_LIMITE_PONCTUALITE).count()
    total_avec_arrivee = presences_avec_arrivee.count()
    taux_retard = round(nb_retards / total_avec_arrivee * 100, 1) if total_avec_arrivee else None

    nb_conges = DemandeConge.objects.filter(
        statut="approuve", date_debut__range=(periode_debut, periode_fin)
    ).count()

    nb_formations = InscriptionFormationRH.objects.filter(
        statut__in=["present", "certifie"], date_inscription__date__range=(periode_debut, periode_fin)
    ).count()

    nb_recrutements = FicheAgent.objects.filter(date_prise_service__range=(periode_debut, periode_fin)).count()
    nb_departs = FicheAgent.objects.filter(date_depart__range=(periode_debut, periode_fin)).count()
    taux_rotation = (
        round((nb_recrutements + nb_departs) / 2 / effectif_total * 100, 1) if effectif_total else None
    )

    diligences_terminees = Diligence.objects.filter(
        statut__in=["termine", "archivee"], updated_at__date__range=(periode_debut, periode_fin)
    ).count()
    productivite_moyenne = round(diligences_terminees / effectif_total, 2) if effectif_total else None

    return {
        "effectif_total": effectif_total,
        "taux_presence": taux_presence,
        "taux_absenteisme": taux_absenteisme,
        "taux_retard": taux_retard,
        "nombre_conges_accordes": nb_conges,
        "nombre_formations_suivies": nb_formations,
        "nombre_recrutements": nb_recrutements,
        "nombre_departs": nb_departs,
        "taux_rotation_personnel": taux_rotation,
        "productivite_moyenne_agent": productivite_moyenne,
    }


class RHKPIDecisionnelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_rh_kpis(date_debut, date_fin))
