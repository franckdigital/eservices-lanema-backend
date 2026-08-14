import json

from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import CompteEmailDFIR, EmailDFIR, PieceJointeEmailDFIR
from .serializers import CompteEmailDFIRSerializer, EmailDFIRListSerializer, EmailDFIRSerializer
from .services import analyser_ia, detect_provider_config, send_email, sync_compte, test_imap_connection, test_smtp_connection

DFIR_DIRECTION = direction_permission('DFIR', feature_key='dfir_view_email')


class CanManageDfirEmail(permissions.BasePermission):
    """La messagerie DFIR est gérée par la direction (Admin/Directeur) ou par
    les formateurs qualifiés (quel que soit leur palier) — pas par
    l'ensemble du personnel encadrement/terrain."""

    def has_permission(self, request, view):
        if DFIR_DIRECTION().has_permission(request, view):
            return True
        user = request.user
        return bool(user and user.is_authenticated and hasattr(user, "formateur_dfir"))


class CompteEmailDFIRViewSet(viewsets.ModelViewSet):
    serializer_class = CompteEmailDFIRSerializer
    permission_classes = [CanManageDfirEmail]

    def get_queryset(self):
        return CompteEmailDFIR.objects.filter(utilisateur=self.request.user)

    @action(detail=True, methods=["post"], url_path="tester-connexion")
    def tester_connexion(self, request, pk=None):
        compte = self.get_object()
        smtp_ok, smtp_detail = test_smtp_connection(compte)
        imap_ok, imap_detail = test_imap_connection(compte)
        success = smtp_ok and imap_ok

        compte.statut = "ACTIF" if success else "ERREUR"
        compte.derniere_erreur = "" if success else f"SMTP : {smtp_detail} | IMAP : {imap_detail}"
        compte.save(update_fields=["statut", "derniere_erreur"])

        return Response({
            "success": success,
            "smtp": {"ok": smtp_ok, "detail": smtp_detail},
            "imap": {"ok": imap_ok, "detail": imap_detail},
        })

    @action(detail=True, methods=["post"])
    def synchroniser(self, request, pk=None):
        compte = self.get_object()
        try:
            nb = sync_compte(compte)
        except Exception as exc:
            compte.statut = "ERREUR"
            compte.derniere_erreur = str(exc)
            compte.save(update_fields=["statut", "derniere_erreur"])
            return Response({"detail": f"Échec de la synchronisation : {exc}"}, status=400)
        return Response({"detail": f"{nb} nouveau(x) message(s) récupéré(s).", "nombre_nouveaux": nb})


class DetecterConfigView(APIView):
    permission_classes = [CanManageDfirEmail]

    def get(self, request):
        email_address = request.query_params.get("email", "")
        return Response({"config": detect_provider_config(email_address)})


class EmailDFIRViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageDfirEmail]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = EmailDFIR.objects.filter(compte__utilisateur=self.request.user).select_related(
            "compte", "en_reponse_a"
        ).prefetch_related("pieces_jointes")
        compte_id = self.request.query_params.get("compte")
        if compte_id:
            qs = qs.filter(compte_id=compte_id)
        statut = self.request.query_params.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return EmailDFIRListSerializer
        return EmailDFIRSerializer

    @staticmethod
    def _parse_list(data, key):
        raw = data.get(key)
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, ValueError):
            return []

    def create(self, request, *args, **kwargs):
        data = request.data
        compte = CompteEmailDFIR.objects.filter(pk=data.get("compte")).first()
        if not compte:
            return Response({"detail": "Compte introuvable."}, status=400)
        if compte.utilisateur_id != request.user.id:
            return Response({"detail": "Ce compte ne vous appartient pas."}, status=403)

        destinataires = self._parse_list(data, "destinataires")
        destinataires_cc = self._parse_list(data, "destinataires_cc")
        if not destinataires:
            return Response({"detail": "Au moins un destinataire requis."}, status=400)

        sujet = data.get("sujet", "") or ""
        corps_texte = data.get("corps_texte", "") or ""
        corps_html = data.get("corps_html", "") or ""
        en_reponse_a_id = data.get("en_reponse_a") or None
        en_reponse_a = EmailDFIR.objects.filter(pk=en_reponse_a_id).first() if en_reponse_a_id else None
        fichiers = request.FILES.getlist("pieces_jointes")

        pieces_pour_envoi = []
        for f in fichiers:
            pieces_pour_envoi.append({"nom": f.name, "contenu": f.read()})
            f.seek(0)

        try:
            message_id = send_email(
                compte, destinataires, sujet, corps_texte, corps_html=corps_html,
                cc=destinataires_cc, en_reponse_a=en_reponse_a, pieces_jointes=pieces_pour_envoi,
            )
        except Exception as exc:
            return Response({"detail": f"Échec de l'envoi : {exc}"}, status=400)

        thread_id = (en_reponse_a.thread_id or en_reponse_a.message_id) if en_reponse_a else message_id
        expediteur_nom = compte.nom_affichage or request.user.get_full_name() or request.user.username

        email_obj = EmailDFIR.objects.create(
            compte=compte, direction="SORTANT", message_id=message_id, thread_id=thread_id,
            en_reponse_a=en_reponse_a, sujet=sujet, expediteur_nom=expediteur_nom,
            expediteur_email=compte.adresse_email, destinataires=destinataires, destinataires_cc=destinataires_cc,
            corps_texte=corps_texte, corps_html=corps_html, date_message=timezone.now(), statut="LU",
            cree_par=request.user,
        )
        if en_reponse_a:
            en_reponse_a.statut = "REPONDU"
            en_reponse_a.save(update_fields=["statut"])

        for f in fichiers:
            pj = PieceJointeEmailDFIR(email=email_obj, nom_fichier=f.name, type_mime=f.content_type or "", taille=f.size)
            pj.fichier.save(f.name, f, save=True)

        return Response(EmailDFIRSerializer(email_obj).data, status=201)

    @action(detail=True, methods=["post"], url_path="marquer-lu")
    def marquer_lu(self, request, pk=None):
        email_obj = self.get_object()
        email_obj.statut = "LU"
        email_obj.save(update_fields=["statut"])
        return Response(EmailDFIRSerializer(email_obj).data)

    @action(detail=True, methods=["post"], url_path="analyser-ia")
    def analyser_ia_action(self, request, pk=None):
        email_obj = self.get_object()
        analyser_ia(email_obj)
        return Response(EmailDFIRSerializer(email_obj).data)
