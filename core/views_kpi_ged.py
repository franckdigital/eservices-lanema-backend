"""KPI decisionnels du module GED (Information & Documentation).

Fichier separe de views.py (deja tres volumineux) et de ged_views.py (qui
expose deja une action `stats` plus basique, consommee par GEDStats.js — on
n'y touche pas pour ne rien casser). Ce nouvel endpoint est uniquement
consomme par le futur tableau de bord "KPI decisionnels"."""
from django.db.models import Avg
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document, DocumentLog, RechercheDocumentaireLog


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

    # Temps moyen de recherche documentaire : moyenne des durées postées par
    # le frontend (RechercheDocumentaireLog), converti ms -> secondes. Reste
    # None tant qu'aucune recherche n'a encore été instrumentée sur la
    # période, auquel cas temps_moyen_recherche_note explique pourquoi.
    recherches = RechercheDocumentaireLog.objects.all()
    if date_debut and date_fin:
        recherches = recherches.filter(created_at__date__range=(date_debut, date_fin))
    moyenne_ms = recherches.aggregate(m=Avg("duree_ms"))["m"]
    temps_moyen_recherche_documentaire = round(moyenne_ms / 1000, 1) if moyenne_ms is not None else None

    return {
        "nombre_documents_enregistres": total,
        "nombre_documents_archives": documents.filter(statut="archive").count(),
        "nombre_consultations_documentaires": nb_consultations,
        "temps_moyen_recherche_documentaire": temps_moyen_recherche_documentaire,
        "temps_moyen_recherche_note": None if temps_moyen_recherche_documentaire is not None else (
            "Pas encore de recherche mesurée sur cette période — la mesure "
            "s'active progressivement à mesure que les utilisateurs effectuent "
            "des recherches dans la GED."
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


class RechercheDocumentaireLogView(APIView):
    """Reçoit du frontend la durée (ms) d'une recherche documentaire, pour
    alimenter le KPI temps_moyen_recherche_documentaire. Voir GedAttachmentPanel
    / DocumentList côté frontend pour l'instrumentation qui poste ici."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        duree_ms = request.data.get("duree_ms")
        if duree_ms is None or int(duree_ms) < 0:
            return Response({"error": "duree_ms requis (entier positif)"}, status=status.HTTP_400_BAD_REQUEST)

        RechercheDocumentaireLog.objects.create(
            utilisateur=request.user,
            terme=(request.data.get("terme") or "")[:255],
            duree_ms=int(duree_ms),
            resultat_trouve=bool(request.data.get("resultat_trouve", True)),
        )
        return Response({"status": "ok"}, status=status.HTTP_201_CREATED)
