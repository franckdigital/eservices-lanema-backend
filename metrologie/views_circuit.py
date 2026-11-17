"""API du circuit metrologie : fiches d'execution des travaux (service reception ->
DMCT) et certificats d'etalonnage (DMCT -> client)."""
import base64

from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from clients.permissions_catalog import user_has_permission
from core.direction_access import is_full_access_user, user_direction_code
from demandes.models import DemandeDevis
from qualite.models import FicheEntreeEquipement

from . import circuit_metro, pdf_metro
from .models import CertificatEtalonnage, EquipementFTM, FicheTravauxMetrologie

ROLES_RECEPTION = ("RECEPTION", "GESTIONNAIRE", "ADMIN")
ROLES_DMCT_LABO = ("TECHNICIEN", "GESTIONNAIRE", "ADMIN")


def _role(user):
    return getattr(getattr(user, "client_profile", None), "role", None)


def _est_reception(user):
    return _role(user) in ROLES_RECEPTION and user_has_permission(user, "echantillons.manage")


def _est_dmct(user):
    """Membre de la DMCT (compte e-diligence) ou personnel labo habilite metrologie."""
    if user_direction_code(user) == "DMCT" or is_full_access_user(user):
        return True
    return _role(user) in ROLES_DMCT_LABO and user_has_permission(user, "metrologie.manage")


def _voir(user):
    if _role(user) == "CLIENT":
        return False
    return _est_reception(user) or _est_dmct(user)


def _exiger(ok, message="Non autorisé"):
    if not ok:
        raise PermissionDenied(message)


def _err(exc):
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


def _pdf(contenu, nom):
    return Response({"filename": nom, "content": base64.b64encode(contenu).decode("ascii")})


class FicheMetrologieViewSet(viewsets.ViewSet):
    """Fiche d'execution des travaux de metrologie (EN 004-PG 002)."""

    permission_classes = [permissions.IsAuthenticated]

    def _fiche(self, pk):
        return FicheTravauxMetrologie.objects.select_related("demande_devis", "demande_devis__client").get(pk=pk)

    def list(self, request):
        _exiger(_voir(request.user))
        qs = FicheTravauxMetrologie.objects.select_related("demande_devis", "demande_devis__client").prefetch_related("certificats")
        p = request.query_params
        if p.get("statut"):
            qs = qs.filter(statut__in=[s for s in p["statut"].split(",") if s])
        if p.get("q"):
            qs = qs.filter(Q(numero__icontains=p["q"]) | Q(demande_devis__numero__icontains=p["q"]))
        if not _est_dmct(request.user):  # la reception ne voit que le suivi
            pass
        return Response([circuit_metro.ftm_resume(f) for f in qs[:200]])

    def retrieve(self, request, pk=None):
        _exiger(_voir(request.user))
        try:
            return Response(circuit_metro.ftm_data(self._fiche(pk)))
        except FicheTravauxMetrologie.DoesNotExist:
            return Response({"detail": "Fiche introuvable"}, status=404)

    @action(detail=False, methods=["get"], url_path="a_etablir")
    def a_etablir(self, request):
        """Demandes de devis de metrologie dont des equipements receptionnes n'ont pas encore de fiche."""
        _exiger(_voir(request.user))
        res = []
        deja = set(EquipementFTM.objects.exclude(fiche_entree=None).values_list("fiche_entree_id", flat=True))
        entrees = FicheEntreeEquipement.objects.filter(domaine="METROLOGIE", demande_devis__isnull=False).exclude(id__in=deja).select_related("demande_devis").order_by("id")
        groupes = {}
        for fe in entrees:
            groupes.setdefault(fe.demande_devis_id, []).append(fe)
        for did, fes in groupes.items():
            devis = fes[0].demande_devis
            cl = circuit_metro.client_info(devis)
            familles = {(e.details or {}).get("famille") for e in devis.echantillons_prevus.all()} - {None, ""}
            grandeur_defaut = next(iter(familles)) if len(familles) == 1 else "AUTRE"
            res.append({
                "demande_devis": did, "devis_numero": devis.numero, "client": cl["raison_sociale"], "code_client": cl["code_client"],
                "lieu_defaut": "SITE_CLIENT" if devis.lieu_realisation == "SITE_CLIENT" else "LABORATOIRE",
                "instruments_devis": [{"nom": e.nom, "quantite": e.quantite, "details": e.details or {}} for e in devis.echantillons_prevus.all()],
                "equipements": [
                    {"id": None, "fiche_entree": fe.id, "code": fe.code, "designation": fe.designation, "constructeur": fe.marque, "modele": fe.modele,
                     "numero_serie": fe.numero_serie, "nature": "Étalonnage", "grandeur": grandeur_defaut, "plage_mesure": "", "resolution": "", "classe": "", "unite": "", "localisation": ""}
                    for fe in fes
                ],
            })
        return Response(res)

    def create(self, request):
        _exiger(_est_reception(request.user), "Seul le service réception peut établir une fiche d'exécution.")
        devis = DemandeDevis.objects.filter(pk=request.data.get("demande_devis")).first()
        if devis is None:
            return Response({"detail": "Demande de devis introuvable."}, status=400)
        try:
            fiche = circuit_metro.creer_ftm(devis, request.data, request.user)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.ftm_data(self._fiche(fiche.pk)), status=201)

    def update(self, request, pk=None):
        _exiger(_est_reception(request.user))
        fiche = self._fiche(pk)
        if fiche.statut != "BROUILLON":
            return Response({"detail": "La fiche a été transmise : elle n'est plus modifiable par la réception."}, status=400)
        try:
            circuit_metro.enregistrer_ftm(fiche, request.data, request.user)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.ftm_data(self._fiche(pk)))

    partial_update = update

    def _etape(self, request, pk, controle, fn, *args):
        _exiger(controle(request.user))
        fiche = self._fiche(pk)
        try:
            fn(fiche, *args)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.ftm_data(self._fiche(pk)))

    @action(detail=True, methods=["post"], url_path="transmettre")
    def transmettre(self, request, pk=None):
        return self._etape(request, pk, _est_reception, circuit_metro.transmettre_ftm, request.user)

    @action(detail=True, methods=["post"], url_path="receptionner")
    def receptionner(self, request, pk=None):
        return self._etape(request, pk, _est_dmct, circuit_metro.receptionner_dmct, request.user)

    @action(detail=True, methods=["post"], url_path="demarrer")
    def demarrer(self, request, pk=None):
        return self._etape(request, pk, _est_dmct, circuit_metro.demarrer_travaux, request.data, request.user)

    @action(detail=True, methods=["post"], url_path="terminer")
    def terminer(self, request, pk=None):
        return self._etape(request, pk, _est_dmct, circuit_metro.terminer_travaux, request.data, request.user)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        _exiger(_voir(request.user))
        fiche = self._fiche(pk)
        return _pdf(pdf_metro.ftm_pdf(fiche), f"FET-Metrologie_{fiche.numero.replace('/', '-')}.pdf")


class CertificatViewSet(viewsets.ViewSet):
    """Certificats d'etalonnage, edites par la DMCT."""

    permission_classes = [permissions.IsAuthenticated]

    def _cert(self, pk):
        return CertificatEtalonnage.objects.select_related("equipement", "fiche", "fiche__demande_devis", "fiche__demande_devis__client", "operateur").get(pk=pk)

    def list(self, request):
        _exiger(_voir(request.user))
        qs = CertificatEtalonnage.objects.select_related("equipement", "fiche", "fiche__demande_devis")
        p = request.query_params
        if p.get("statut"):
            qs = qs.filter(statut__in=[s for s in p["statut"].split(",") if s])
        if p.get("fiche"):
            qs = qs.filter(fiche_id=p["fiche"])
        if p.get("q"):
            qs = qs.filter(Q(numero__icontains=p["q"]) | Q(equipement__designation__icontains=p["q"]))
        res = []
        for c in qs[:300]:
            res.append({
                "id": c.id, "numero": c.numero, "statut": c.statut, "statut_display": c.get_statut_display(), "designation": c.equipement.designation,
                "code": c.equipement.code, "numero_serie": c.equipement.numero_serie, "fiche_numero": c.fiche.numero,
                "client": circuit_metro.client_info(c.fiche.demande_devis)["raison_sociale"], "date_emission": c.date_emission,
            })
        return Response(res)

    def retrieve(self, request, pk=None):
        _exiger(_voir(request.user))
        try:
            return Response(circuit_metro.certificat_data(self._cert(pk)))
        except CertificatEtalonnage.DoesNotExist:
            return Response({"detail": "Certificat introuvable"}, status=404)

    def create(self, request):
        """Prepare le certificat (brouillon) d'un equipement de la fiche."""
        _exiger(_est_dmct(request.user), "Seule la DMCT peut préparer un certificat.")
        eq = EquipementFTM.objects.select_related("fiche").filter(pk=request.data.get("equipement")).first()
        if eq is None:
            return Response({"detail": "Équipement introuvable."}, status=400)
        try:
            c = circuit_metro.creer_certificat(eq, request.user)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.certificat_data(self._cert(c.pk)), status=201)

    def partial_update(self, request, pk=None):
        _exiger(_est_dmct(request.user))
        c = self._cert(pk)
        try:
            circuit_metro.enregistrer_certificat(c, request.data, request.user)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.certificat_data(self._cert(pk)))

    update = partial_update

    def _etape(self, request, pk, fn, *args):
        _exiger(_est_dmct(request.user))
        c = self._cert(pk)
        try:
            fn(c, *args)
        except ValueError as exc:
            return _err(exc)
        return Response(circuit_metro.certificat_data(self._cert(pk)))

    @action(detail=True, methods=["post"], url_path="editer")
    def editer(self, request, pk=None):
        return self._etape(request, pk, circuit_metro.editer_certificat, request.user)

    @action(detail=True, methods=["post"], url_path="signer")
    def signer(self, request, pk=None):
        return self._etape(request, pk, circuit_metro.signer_certificat)

    @action(detail=True, methods=["post"], url_path="transmettre")
    def transmettre(self, request, pk=None):
        return self._etape(request, pk, circuit_metro.transmettre_certificat)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        _exiger(_voir(request.user))
        c = self._cert(pk)
        return _pdf(pdf_metro.certificat_pdf(c), f"CertificatEtalonnage_{(c.numero or 'projet-' + str(c.pk)).replace('/', '-')}.pdf")


class MesCertificatsViewSet(viewsets.ViewSet):
    """Espace client : certificats d'etalonnage transmis au client."""

    permission_classes = [permissions.IsAuthenticated]

    def _qs(self, request):
        return CertificatEtalonnage.objects.filter(statut="TRANSMIS", fiche__demande_devis__client=request.user).select_related("equipement", "fiche")

    def list(self, request):
        return Response([
            {"id": c.id, "numero": c.numero, "designation": c.equipement.designation, "numero_serie": c.equipement.numero_serie,
             "code": c.equipement.code, "grandeur": c.get_grandeur_display(), "date_emission": c.date_emission, "date_transmission": c.date_transmission,
             "decision": c.equipement.decision, "fiche_numero": c.fiche.numero}
            for c in self._qs(request)
        ])

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        c = self._qs(request).filter(pk=pk).first()
        if c is None:
            return Response({"detail": "Certificat introuvable"}, status=404)
        return _pdf(pdf_metro.certificat_pdf(c), f"CertificatEtalonnage_{c.numero.replace('/', '-')}.pdf")
