"""KPI decisionnels du module GED (Information & Documentation).

Fichier separe de views.py (deja tres volumineux) et de ged_views.py (qui
expose deja une action `stats` plus basique, consommee par GEDStats.js — on
n'y touche pas pour ne rien casser). Ce nouvel endpoint est uniquement
consomme par le futur tableau de bord "KPI decisionnels"."""
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document, DocumentLog


def compute_ged_kpis(date_debut=None, date_fin=None):
    documents = Document.objects.filter(est_supprime=False)
    if date_debut and date_fin:
        documents = documents.filter(created_at__date__range=(date_debut, date_fin))

    total = documents.count()
    logs = DocumentLog.objects.filter(document__in=documents)

    nb_consultations = logs.filter(action__in=["consultation", "telechargement"]).count()
    nb_archives_consultees = logs.filter(
        document__statut="archive", action__in=["consultation", "telechargement"]
    ).count()

    aujourd_hui = timezone.now().date()
    nb_expires = documents.filter(date_expiration__lt=aujourd_hui).count()

    nb_disponibles = documents.exclude(statut="brouillon").count()
    taux_disponibilite = round(nb_disponibles / total * 100, 1) if total else None

    nb_numerises = documents.exclude(fichier="").count()
    taux_numerisation = round(nb_numerises / total * 100, 1) if total else None

    return {
        "nombre_documents_enregistres": total,
        "nombre_documents_archives": documents.filter(statut="archive").count(),
        "nombre_consultations_documentaires": nb_consultations,
        "temps_moyen_recherche_documentaire": None,
        "temps_moyen_recherche_note": (
            "Non mesurable avec les donnees actuelles : aucune instrumentation "
            "du temps de recherche cote frontend/API."
        ),
        "nombre_documents_diffuses": documents.filter(statut="diffuse").count(),
        "nombre_documents_expires": nb_expires,
        "taux_disponibilite_documents": taux_disponibilite,
        "taux_numerisation": taux_numerisation,
        "nombre_archives_consultees": nb_archives_consultees,
        "nombre_documents_corbeille": Document.objects.filter(est_supprime=True).count(),
        "nombre_documents_rattaches_hors_courrier": documents.filter(content_type__isnull=False).count(),
    }


class GedKPIDecisionnelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_ged_kpis(date_debut, date_fin))
