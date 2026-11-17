"""API du circuit reception <-> laboratoire : fiches d'execution des travaux
(FET) et rapports d'essai officiels."""
import base64

from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from clients.permissions_catalog import user_has_permission
from facturation.models import DemandeAnalyse

from . import circuit, pdf_circuit
from .models import Echantillon, FicheExecutionTravaux, RapportEssaiLabo

ROLES_RECEPTION = ("RECEPTION", "GESTIONNAIRE", "ADMIN")
ROLES_LABO = ("TECHNICIEN", "GESTIONNAIRE", "ADMIN")


def _role(user):
    return getattr(getattr(user, "client_profile", None), "role", None)


def _voir(user):
    if _role(user) in (None, "CLIENT", "FOURNISSEUR"):
        return False
    return user_has_permission(user, "echantillons.view") or user_has_permission(user, "essais.view")


def _reception(user):
    return _role(user) in ROLES_RECEPTION and user_has_permission(user, "echantillons.manage")


def _labo(user):
    return _role(user) in ROLES_LABO and user_has_permission(user, "essais.manage")


def _exiger(ok, message):
    if not ok:
        raise PermissionDenied(message)


def _err(exc):
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


def _pdf_response(contenu, nom):
    return Response({"filename": nom, "content": base64.b64encode(contenu).decode("ascii")})


class FicheTravauxViewSet(viewsets.ViewSet):
    """Fiche d'execution des travaux d'essais (EN 003-PG 002)."""

    permission_classes = [permissions.IsAuthenticated]

    def _fiche(self, request, pk):
        _exiger(_voir(request.user), "Non autorisé")
        return FicheExecutionTravaux.objects.select_related("demande", "demande__client").get(pk=pk)

    def list(self, request):
        _exiger(_voir(request.user), "Non autorisé")
        qs = FicheExecutionTravaux.objects.select_related("demande", "demande__client").prefetch_related("suivis_labo__laboratoire", "rapports__laboratoire")
        p = request.query_params
        if p.get("statut"):
            qs = qs.filter(statut__in=[s for s in p["statut"].split(",") if s])
        if p.get("laboratoire"):
            qs = qs.filter(suivis_labo__laboratoire_id=p["laboratoire"]).exclude(statut="BROUILLON").distinct()
        if p.get("demande"):
            qs = qs.filter(demande_id=p["demande"])
        if p.get("q"):
            qs = qs.filter(Q(numero__icontains=p["q"]) | Q(demande__numero__icontains=p["q"]))
        return Response([circuit.fiche_resume(f) for f in qs[:200]])

    def retrieve(self, request, pk=None):
        try:
            fiche = self._fiche(request, pk)
        except FicheExecutionTravaux.DoesNotExist:
            return Response({"detail": "Fiche introuvable"}, status=404)
        return Response(circuit.fiche_data(fiche))

    def create(self, request):
        _exiger(_reception(request.user), "Seul le service réception peut établir une fiche d'exécution des travaux.")
        demande = DemandeAnalyse.objects.filter(pk=request.data.get("demande")).first()
        if demande is None:
            return Response({"detail": "Demande d'analyse introuvable."}, status=400)
        try:
            fiche = circuit.creer_fiche(demande, request.data, request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche), status=201)

    def update(self, request, pk=None):
        _exiger(_reception(request.user), "Non autorisé")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        if fiche.statut != "BROUILLON":
            return Response({"detail": "La fiche a été transmise : elle n'est plus modifiable."}, status=400)
        try:
            circuit.enregistrer_fiche(fiche, request.data, request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    partial_update = update

    @action(detail=False, methods=["get"], url_path="a_etablir")
    def a_etablir(self, request):
        """Demandes d'analyse dont des echantillons receptionnes n'ont pas encore de fiche."""
        _exiger(_voir(request.user), "Non autorisé")
        res = []
        for d in DemandeAnalyse.objects.filter(statut__in=["ECHANTILLONS_RECUS", "EN_COURS", "EN_ATTENTE_ECHANTILLONS"]).select_related("client"):
            libres = Echantillon.objects.filter(demande=d, fiche__isnull=True).order_by("id")
            if libres.exists():
                profil = getattr(d.client, "client_profile", None)
                res.append({
                    "demande": d.id, "demande_numero": d.numero, "client": getattr(profil, "raison_sociale", "") or d.client.username,
                    "code_client": getattr(profil, "code_client", "") or "",
                    "nature_defaut": {"EAUX_CONSOMMATION": "EAUX", "SOLS_ENGRAIS": "AUTRES"}.get(d.demande_devis.type_analyse, "ALIMENTAIRE"),
                    "echantillons": [
                        {"id": e.id, "code_echantillon": e.code_echantillon, "designation": e.designation, "quantite": e.quantite,
                         "description": e.description, "date_prelevement": e.date_prelevement, "etat": e.etat or [], "etat_precision": e.etat_precision,
                         "parametres": e.parametres, "laboratoires": [], "lieu_prelevement": e.lieu_prelevement, "prelevement_par": e.prelevement_par,
                         "numero_lot": e.numero_lot, "date_heure_prelevement": None}
                        for e in libres
                    ],
                })
        return Response(res)

    @action(detail=True, methods=["post"], url_path="transmettre")
    def transmettre(self, request, pk=None):
        _exiger(_reception(request.user), "Non autorisé")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        if fiche.statut != "BROUILLON":
            return Response({"detail": "Cette fiche a déjà été transmise."}, status=400)
        try:
            circuit.transmettre_au_laboratoire(fiche, request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    @action(detail=True, methods=["post"], url_path="receptionner_labo")
    def receptionner_labo(self, request, pk=None):
        _exiger(_labo(request.user), "Seul le personnel du laboratoire peut réceptionner la fiche.")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        try:
            circuit.receptionner_labo(fiche, request.data.get("laboratoire"), request.data.get("acceptation"), request.data.get("reserves"), request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    @action(detail=True, methods=["post"], url_path="resultats")
    def resultats(self, request, pk=None):
        _exiger(_labo(request.user), "Seul le personnel du laboratoire peut saisir des résultats.")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        try:
            circuit.saisir_resultats(fiche, request.data.get("laboratoire"), request.data.get("resultats") or [], request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    @action(detail=True, methods=["post"], url_path="transmettre_resultats")
    def transmettre_resultats(self, request, pk=None):
        _exiger(_labo(request.user), "Non autorisé")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        try:
            circuit.transmettre_resultats(fiche, request.data.get("laboratoire"), request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    @action(detail=True, methods=["post"], url_path="recevoir_resultats")
    def recevoir_resultats(self, request, pk=None):
        _exiger(_reception(request.user), "Non autorisé")
        fiche = FicheExecutionTravaux.objects.get(pk=pk)
        try:
            circuit.recevoir_resultats(fiche, request.user)
        except ValueError as exc:
            return _err(exc)
        fiche.refresh_from_db()
        return Response(circuit.fiche_data(fiche))

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        fiche = self._fiche(request, pk)
        return _pdf_response(pdf_circuit.fet_pdf(fiche), f"FET_{fiche.numero.replace('/', '-')}.pdf")


class RapportEssaiViewSet(viewsets.ViewSet):
    """Rapports d'essai officiels (EN 001-PG019), edites par le service reception."""

    permission_classes = [permissions.IsAuthenticated]

    def _rapport(self, request, pk):
        _exiger(_voir(request.user), "Non autorisé")
        return RapportEssaiLabo.objects.select_related("fiche", "fiche__demande", "fiche__demande__client", "laboratoire").get(pk=pk)

    def list(self, request):
        _exiger(_voir(request.user), "Non autorisé")
        qs = RapportEssaiLabo.objects.select_related("fiche", "fiche__demande", "laboratoire")
        p = request.query_params
        if p.get("statut"):
            qs = qs.filter(statut__in=[s for s in p["statut"].split(",") if s])
        if p.get("fiche"):
            qs = qs.filter(fiche_id=p["fiche"])
        if p.get("q"):
            qs = qs.filter(Q(reference__icontains=p["q"]) | Q(fiche__numero__icontains=p["q"]))
        res = []
        for r in qs[:300]:
            profil = getattr(r.fiche.demande.client, "client_profile", None)
            res.append({
                "id": r.id, "reference": r.reference, "statut": r.statut, "statut_display": r.get_statut_display(),
                "laboratoire_code": r.laboratoire.code, "laboratoire_nom": r.laboratoire.nom, "fiche_numero": r.fiche.numero,
                "demande_numero": r.fiche.demande.numero, "client": getattr(profil, "raison_sociale", "") or r.fiche.demande.client.username,
                "date_edition": r.date_edition, "numero_ordre": r.numero_ordre,
            })
        return Response(res)

    def retrieve(self, request, pk=None):
        try:
            return Response(circuit.rapport_data(self._rapport(request, pk)))
        except RapportEssaiLabo.DoesNotExist:
            return Response({"detail": "Rapport introuvable"}, status=404)

    def partial_update(self, request, pk=None):
        _exiger(_reception(request.user), "Non autorisé")
        rapport = RapportEssaiLabo.objects.get(pk=pk)
        if rapport.statut != "BROUILLON":
            return Response({"detail": "Le rapport est édité : il n'est plus modifiable."}, status=400)
        for champ in ("informations_diverses", "directeur_nom"):
            if champ in request.data:
                setattr(rapport, champ, (request.data.get(champ) or "")[:2000])
        rapport.save()
        return Response(circuit.rapport_data(rapport))

    update = partial_update

    @action(detail=True, methods=["post"], url_path="editer")
    def editer(self, request, pk=None):
        _exiger(_reception(request.user), "Seul le service réception édite les rapports d'essai.")
        rapport = RapportEssaiLabo.objects.get(pk=pk)
        try:
            circuit.editer_rapport(rapport, request.user)
        except ValueError as exc:
            return _err(exc)
        rapport.refresh_from_db()
        return Response(circuit.rapport_data(rapport))

    @action(detail=True, methods=["post"], url_path="signer")
    def signer(self, request, pk=None):
        """Enregistre la signature du Directeur sur le rapport edite."""
        _exiger(_reception(request.user), "Non autorisé")
        rapport = RapportEssaiLabo.objects.get(pk=pk)
        if rapport.statut != "EDITE":
            return Response({"detail": "Le rapport doit être édité avant d'être signé."}, status=400)
        rapport.statut = "SIGNE"
        rapport.date_signature = timezone.now().date()
        rapport.save(update_fields=["statut", "date_signature", "updated_at"])
        return Response(circuit.rapport_data(rapport))

    @action(detail=True, methods=["post"], url_path="remettre")
    def remettre(self, request, pk=None):
        _exiger(_reception(request.user), "Non autorisé")
        rapport = RapportEssaiLabo.objects.get(pk=pk)
        try:
            circuit.remettre_rapport(rapport)
        except ValueError as exc:
            return _err(exc)
        rapport.refresh_from_db()
        return Response(circuit.rapport_data(rapport))

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        rapport = self._rapport(request, pk)
        nom = (rapport.reference or f"projet-{rapport.pk}").replace("/", "-")
        return _pdf_response(pdf_circuit.rapport_pdf(rapport), f"RapportEssai_{nom}.pdf")
