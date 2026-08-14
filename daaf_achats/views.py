from django.db.models import Avg
from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BonCommande, DemandeAchat, Fournisseur, Marche
from .serializers import BonCommandeSerializer, DemandeAchatSerializer, FournisseurSerializer, MarcheSerializer


def compute_achats_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI Achats. Reutilisable directement par le tableau de bord DAAF."""
    demandes = DemandeAchat.objects.all()
    bons = BonCommande.objects.all()
    if date_debut and date_fin:
        demandes = demandes.filter(date_demande__range=(date_debut, date_fin))
        bons = bons.filter(date_commande__range=(date_debut, date_fin))

    demandes_traitees = demandes.filter(date_traitement__isnull=False)
    delai_moyen_traitement = None
    if demandes_traitees.exists():
        delais = [(d.date_traitement - d.date_demande).days for d in demandes_traitees]
        delai_moyen_traitement = round(sum(delais) / len(delais), 1)

    marches = Marche.objects.all()
    nb_marches = marches.count()
    nb_marches_conformes = marches.filter(respect_plan=True).count()
    taux_respect_plan = round(nb_marches_conformes / nb_marches * 100, 1) if nb_marches else None

    bons_livres = bons.filter(date_livraison_reelle__isnull=False)
    delai_moyen_livraison = None
    if bons_livres.exists():
        delais = [(b.date_livraison_reelle - b.date_commande).days for b in bons_livres]
        delai_moyen_livraison = round(sum(delais) / len(delais), 1)

    bons_avec_conformite = bons.exclude(conforme__isnull=True)
    nb_conformes = bons_avec_conformite.filter(conforme=True).count()
    taux_conformite_livraisons = (
        round(nb_conformes / bons_avec_conformite.count() * 100, 1) if bons_avec_conformite.exists() else None
    )

    satisfaction_moyenne = bons.filter(note_satisfaction__isnull=False).aggregate(m=Avg("note_satisfaction"))["m"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    today = timezone.now().date()
    nb_commandes_en_retard = bons.filter(
        date_livraison_reelle__isnull=True, date_livraison_prevue__lt=today
    ).exclude(statut__in=["LIVRE", "ANNULE"]).count()

    return {
        "nombre_demandes_achat": demandes.count(),
        "nombre_bons_commande": bons.count(),
        "delai_moyen_traitement_demande_jours": delai_moyen_traitement,
        "nombre_marches_attribues": nb_marches,
        "taux_respect_plan_passation": taux_respect_plan,
        "nombre_fournisseurs_actifs": Fournisseur.objects.filter(actif=True).count(),
        "delai_moyen_livraison_jours": delai_moyen_livraison,
        "taux_conformite_livraisons": taux_conformite_livraisons,
        "taux_satisfaction_utilisateurs": taux_satisfaction,
        "nombre_commandes_en_retard": nb_commandes_en_retard,
    }


class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    permission_classes = [permissions.IsAuthenticated]


class DemandeAchatViewSet(viewsets.ModelViewSet):
    queryset = DemandeAchat.objects.select_related("direction", "demandeur").all()
    serializer_class = DemandeAchatSerializer
    permission_classes = [permissions.IsAuthenticated]


class BonCommandeViewSet(viewsets.ModelViewSet):
    queryset = BonCommande.objects.select_related("demande").all()
    serializer_class = BonCommandeSerializer
    permission_classes = [permissions.IsAuthenticated]


class MarcheViewSet(viewsets.ModelViewSet):
    queryset = Marche.objects.all()
    serializer_class = MarcheSerializer
    permission_classes = [permissions.IsAuthenticated]


class AchatsKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_achats_kpis(date_debut, date_fin))
