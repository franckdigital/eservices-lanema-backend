from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_dashboard.mixins import HistoriqueMixin, log_historique_dae
from aero_maintenance.models import OrdreTravail
from aero_stock.models import PieceRechange
from core.direction_access import direction_permission
from core.pdf_utils import create_pdf_response

from .models import TAUX_HORAIRE_DAE, BonCommandeDAE, DevisDAE, FactureDAE
from .pdf_utils import generate_facture_dae_pdf
from .serializers import BonCommandeDAESerializer, DevisDAESerializer, FactureDAESerializer

# Les documents financiers (devis, bons de commande, factures) sont réservés
# au palier "direction" (Admin/Directeur uniquement). L'agrégat KPI reste
# ouvert à tout membre DAE, comme les autres endpoints KPI.
DAE_DIRECTION = direction_permission('DAE', feature_key='dae_view_finance')
DAE_MEMBRE = direction_permission('DAE')

# Transitions simples devis/bon de commande — mêmes principes que
# TRANSITIONS_OT (aero_maintenance/views.py) et TRANSITIONS (core/ged_views.py).
TRANSITIONS_DEVIS = {
    "BROUILLON": ["ENVOYE"],
    "ENVOYE": ["ACCEPTE", "REFUSE", "EXPIRE"],
    "ACCEPTE": [],
    "REFUSE": [],
    "EXPIRE": [],
}
TRANSITIONS_BON_COMMANDE = {
    "EN_ATTENTE": ["SIGNE", "ANNULE"],
    "SIGNE": [],
    "ANNULE": [],
}


def compute_financiers_kpis(date_debut=None, date_fin=None):
    """Calcule les KPI Financiers de la DAE (categorie 10 + KPI 23-27 du
    cahier des charges section 24 : CA, CA par client, CA par prestation,
    coût moyen d'intervention, marge par prestation). Reutilisable
    directement par le tableau de bord DAE."""
    factures = FactureDAE.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_emission__range=(date_debut, date_fin))

    factures_payees = factures.filter(statut="PAYEE")
    ca_prestations = float(factures_payees.aggregate(t=Sum("montant_ttc"))["t"] or 0)

    ca_par_client = list(
        factures_payees.select_related("client").values("client__nom")
        .annotate(montant=Sum("montant_ttc")).order_by("-montant")
    )
    ca_par_client = [{"client": c["client__nom"], "montant": float(c["montant"] or 0)} for c in ca_par_client]

    ca_par_prestation = {code: 0.0 for code, _ in OrdreTravail.TYPE_CHOICES}
    for f in factures_payees.select_related("ordre_travail"):
        if f.ordre_travail_id:
            ca_par_prestation[f.ordre_travail.type_intervention] = round(
                ca_par_prestation[f.ordre_travail.type_intervention] + float(f.montant_ttc), 2
            )

    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))
    termines = ordres.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"])

    # Cout reel calcule depuis les pieces effectivement consommees pendant
    # les interventions (InterventionTechnique.pieces_utilisees), plutot que
    # depuis l'ancien champ unique OrdreTravail.piece_utilisee (conserve pour
    # compatibilite mais plus alimente par le nouveau flux).
    couts_ordres = []
    cout_par_type = {code: 0.0 for code, _ in OrdreTravail.TYPE_CHOICES}
    for ot in termines.prefetch_related("interventions__pieces_utilisees"):
        cout_ot = sum(
            float(p.prix_unitaire)
            for interv in ot.interventions.all()
            for p in interv.pieces_utilisees.all()
        )
        if cout_ot:
            couts_ordres.append(cout_ot)
            cout_par_type[ot.type_intervention] = round(cout_par_type[ot.type_intervention] + cout_ot, 2)

    cout_moyen_intervention = round(sum(couts_ordres) / len(couts_ordres), 2) if couts_ordres else None
    cout_total = sum(couts_ordres)

    rentabilite = round(ca_prestations - cout_total, 2)

    nb_termines = termines.count()
    taux_facturation = round(factures.count() / nb_termines * 100, 1) if nb_termines else None

    total_factures = factures.count()
    taux_recouvrement = (
        round(factures.filter(statut="PAYEE").count() / total_factures * 100, 1) if total_factures else None
    )

    marge_par_prestation = {
        code: round(ca_par_prestation[code] - cout_par_type[code], 2) for code, _ in OrdreTravail.TYPE_CHOICES
    }

    return {
        "ca_prestations": ca_prestations,
        "ca_par_client": ca_par_client,
        "ca_par_prestation": ca_par_prestation,
        "cout_moyen_intervention": cout_moyen_intervention,
        "cout_maintenance_par_type": cout_par_type,
        "marge_par_prestation": marge_par_prestation,
        "rentabilite": rentabilite,
        "taux_facturation": taux_facturation,
        "taux_recouvrement": taux_recouvrement,
    }


class DevisDAEViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = DevisDAE.objects.select_related("client", "ordre_travail").all()
    serializer_class = DevisDAESerializer
    permission_classes = [DAE_DIRECTION]

    def perform_create(self, serializer):
        last_id = DevisDAE.objects.count() + 1
        instance = serializer.save(reference=f"DEV-DAE-{timezone.now().year}-{last_id:05d}")
        log_historique_dae(instance, self.request.user, "Créé")

    @action(detail=True, methods=["post"], url_path="changer-statut")
    def changer_statut(self, request, pk=None):
        devis = self.get_object()
        nouveau_statut = request.data.get("statut")
        if nouveau_statut not in dict(DevisDAE.STATUT_CHOICES):
            return Response({"error": "Statut invalide."}, status=400)
        if nouveau_statut not in TRANSITIONS_DEVIS.get(devis.statut, []):
            return Response({"error": f"Transition {devis.statut} → {nouveau_statut} non autorisée."}, status=400)
        ancien_statut = devis.statut
        devis.statut = nouveau_statut
        devis.save(update_fields=["statut"])
        log_historique_dae(devis, request.user, "Statut modifié", ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut)
        return Response(DevisDAESerializer(devis).data)

    @action(detail=True, methods=["post"], url_path="generer-bon-commande")
    def generer_bon_commande(self, request, pk=None):
        devis = self.get_object()
        if devis.statut != "ACCEPTE":
            return Response({"error": "Seul un devis accepté peut générer un bon de commande."}, status=400)
        last_id = BonCommandeDAE.objects.count() + 1
        bon = BonCommandeDAE.objects.create(
            reference=f"BC-DAE-{timezone.now().year}-{last_id:05d}",
            devis=devis, ordre_travail=devis.ordre_travail, client=devis.client,
            montant_ttc=devis.montant_ttc,
        )
        log_historique_dae(bon, request.user, "Créé (depuis devis)", nouvelle_valeur=devis.reference)
        return Response(BonCommandeDAESerializer(bon).data, status=201)


class BonCommandeDAEViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = BonCommandeDAE.objects.select_related("client", "devis", "ordre_travail").all()
    serializer_class = BonCommandeDAESerializer
    permission_classes = [DAE_DIRECTION]

    def perform_create(self, serializer):
        last_id = BonCommandeDAE.objects.count() + 1
        instance = serializer.save(reference=f"BC-DAE-{timezone.now().year}-{last_id:05d}")
        log_historique_dae(instance, self.request.user, "Créé")

    @action(detail=True, methods=["post"], url_path="changer-statut")
    def changer_statut(self, request, pk=None):
        bon = self.get_object()
        nouveau_statut = request.data.get("statut")
        if nouveau_statut not in dict(BonCommandeDAE.STATUT_CHOICES):
            return Response({"error": "Statut invalide."}, status=400)
        if nouveau_statut not in TRANSITIONS_BON_COMMANDE.get(bon.statut, []):
            return Response({"error": f"Transition {bon.statut} → {nouveau_statut} non autorisée."}, status=400)
        ancien_statut = bon.statut
        bon.statut = nouveau_statut
        if nouveau_statut == "SIGNE" and not bon.date_signature:
            bon.date_signature = timezone.now().date()
        bon.save(update_fields=["statut", "date_signature"])
        log_historique_dae(bon, request.user, "Statut modifié", ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut)
        return Response(BonCommandeDAESerializer(bon).data)


class FactureDAEViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = FactureDAE.objects.select_related("client", "ordre_travail", "bon_commande").all()
    serializer_class = FactureDAESerializer
    permission_classes = [DAE_DIRECTION]

    def perform_create(self, serializer):
        last_id = FactureDAE.objects.count() + 1
        instance = serializer.save(reference=f"FACT-DAE-{timezone.now().year}-{last_id:05d}")
        instance.recalculer_totaux()
        instance.save(update_fields=["montant_ht", "montant_ttc"])
        log_historique_dae(instance, self.request.user, "Créée")

    def perform_update(self, serializer):
        instance = self.get_object()
        ancien_statut = instance.statut
        updated = serializer.save()
        updated.recalculer_totaux()
        updated.save(update_fields=["montant_ht", "montant_ttc"])
        if ancien_statut != updated.statut:
            log_historique_dae(updated, self.request.user, "Statut modifié", ancienne_valeur=ancien_statut, nouvelle_valeur=updated.statut)

    @action(detail=False, methods=["post"], url_path="generer-depuis-ot")
    def generer_depuis_ot(self, request):
        """Calcule automatiquement la facture depuis les donnees reelles de
        l'OT : temps passe (InterventionTechnique) x taux horaire pour la
        main d'oeuvre, prix des pieces reellement consommees pour les pieces
        — cf. cahier des charges section 20 et 32 (donnees calculees, pas
        ressaisies)."""
        ot_id = request.data.get("ordre_travail")
        try:
            ot = OrdreTravail.objects.select_related("aeronef__client").prefetch_related("interventions__pieces_utilisees").get(pk=ot_id)
        except OrdreTravail.DoesNotExist:
            return Response({"error": "Ordre de travail introuvable."}, status=404)
        if not ot.aeronef or not ot.aeronef.client:
            return Response({"error": "Aucun client rattaché à l'aéronef de cet OT."}, status=400)

        temps_total_minutes = sum(i.temps_passe_minutes for i in ot.interventions.all())
        montant_main_oeuvre = (Decimal(temps_total_minutes) / 60) * TAUX_HORAIRE_DAE

        pieces_ids = set()
        for interv in ot.interventions.all():
            pieces_ids.update(p.id for p in interv.pieces_utilisees.all())
        montant_pieces = sum(
            (p.prix_unitaire for p in PieceRechange.objects.filter(id__in=pieces_ids)), Decimal("0")
        )

        frais_supplementaires = Decimal(str(request.data.get("frais_supplementaires", "0") or "0"))
        taux_tva = Decimal(str(request.data.get("taux_tva", "18") or "18"))

        last_id = FactureDAE.objects.count() + 1
        facture = FactureDAE(
            reference=f"FACT-DAE-{timezone.now().year}-{last_id:05d}",
            ordre_travail=ot, client=ot.aeronef.client,
            montant_main_oeuvre=montant_main_oeuvre, montant_pieces=montant_pieces,
            frais_supplementaires=frais_supplementaires, taux_tva=taux_tva,
        )
        facture.recalculer_totaux()
        facture.save()
        log_historique_dae(
            facture, request.user, "Créée (générée depuis OT)",
            nouvelle_valeur=f"{ot.reference} — {temps_total_minutes} min, {len(pieces_ids)} pièce(s)",
        )
        return Response(FactureDAESerializer(facture).data, status=201)

    @action(detail=True, methods=["get"], url_path="telecharger-pdf")
    def telecharger_pdf(self, request, pk=None):
        facture = self.get_object()
        buffer = generate_facture_dae_pdf(facture)
        return create_pdf_response(buffer, f"facture_{facture.reference}.pdf")


class FinanciersKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_financiers_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
