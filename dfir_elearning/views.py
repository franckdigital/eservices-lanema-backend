import io
import uuid as uuid_lib

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission
from dfir_formations.models import Formation, InscriptionParticipant
from dfir_participants.serializers import ParticipantAuthProfileSerializer

from .models import CertificatFormation, ClasseVirtuelle, Lecon, ProgressionLecon
from .serializers import (
    CertificatFormationSerializer,
    CertificatParticipantSerializer,
    CertificatVerifySerializer,
    ClasseVirtuelleParticipantSerializer,
    ClasseVirtuelleSerializer,
    LeconParticipantSerializer,
    LeconSerializer,
    ProgressionMiniSerializer,
)

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')


class IsParticipant(permissions.BasePermission):
    """Compte "mon espace" (participant e-learning), distinct des comptes
    e-diligence/labo — n'a pas de core.UserProfile."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and hasattr(user, "participant_dfir_profile"))


# ── Gestion (staff, encadrement DFIR) ──────────────────────────────────────

class LeconViewSet(viewsets.ModelViewSet):
    queryset = Lecon.objects.select_related("formation").all()
    serializer_class = LeconSerializer
    permission_classes = [DFIR_ENCADREMENT]


class ClasseVirtuelleViewSet(viewsets.ModelViewSet):
    queryset = ClasseVirtuelle.objects.select_related("session__formation").all()
    serializer_class = ClasseVirtuelleSerializer
    permission_classes = [DFIR_ENCADREMENT]


class CertificatFormationViewSet(viewsets.ModelViewSet):
    queryset = CertificatFormation.objects.select_related(
        "inscription__participant", "inscription__session__formation"
    ).all()
    serializer_class = CertificatFormationSerializer
    permission_classes = [DFIR_ENCADREMENT]

    def perform_create(self, serializer):
        # Place-holder unique le temps d'obtenir le pk, puis numéro définitif.
        instance = serializer.save(numero=f"TEMP-{uuid_lib.uuid4().hex[:12]}")
        instance.numero = f"CERT-DFIR-{instance.pk:06d}"
        instance.save(update_fields=["numero"])


# ── "Mon espace" (participant authentifié) ─────────────────────────────────

class MonEspaceView(APIView):
    permission_classes = [IsParticipant]

    def get(self, request):
        participant = request.user.participant_dfir_profile
        inscriptions = InscriptionParticipant.objects.filter(
            participant=participant, abandon=False
        ).select_related("session__formation")

        session_ids = list(inscriptions.values_list("session_id", flat=True))
        formation_ids = inscriptions.values_list("session__formation_id", flat=True).distinct()
        formations = Formation.objects.filter(id__in=formation_ids).prefetch_related("lecons")

        formations_data = []
        for formation in formations:
            lecons = formation.lecons.all()
            formations_data.append({
                "id": formation.id,
                "titre": formation.titre,
                "type_formation": formation.type_formation,
                "certifiante": formation.certifiante,
                "lecons": LeconParticipantSerializer(lecons, many=True, context={"participant": participant}).data,
            })

        classes = ClasseVirtuelle.objects.filter(session_id__in=session_ids).select_related("session__formation")
        certificats = CertificatFormation.objects.filter(
            inscription__participant=participant
        ).select_related("inscription__session__formation")

        return Response({
            "participant": ParticipantAuthProfileSerializer(participant).data,
            "formations": formations_data,
            "classes_virtuelles": ClasseVirtuelleParticipantSerializer(classes, many=True).data,
            "certificats": CertificatParticipantSerializer(certificats, many=True).data,
        })


class ProgressionUpdateView(APIView):
    permission_classes = [IsParticipant]

    def post(self, request, lecon_id):
        participant = request.user.participant_dfir_profile
        try:
            lecon = Lecon.objects.select_related("formation").get(id=lecon_id)
        except Lecon.DoesNotExist:
            return Response({"detail": "Leçon introuvable"}, status=404)

        has_access = InscriptionParticipant.objects.filter(
            participant=participant, abandon=False, session__formation=lecon.formation
        ).exists()
        if not has_access:
            return Response({"detail": "Vous n'avez pas accès à cette leçon"}, status=403)

        progression, _ = ProgressionLecon.objects.get_or_create(participant=participant, lecon=lecon)
        data = request.data or {}
        if "vu" in data:
            progression.vu = bool(data["vu"])
            if progression.vu and not progression.date_vu:
                progression.date_vu = timezone.now()
        if "note_personnelle" in data:
            progression.note_personnelle = str(data["note_personnelle"])[:5000]
        progression.save()
        return Response(ProgressionMiniSerializer(progression).data)


class CertificatPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            certificat = CertificatFormation.objects.select_related(
                "inscription__participant", "inscription__session__formation"
            ).get(pk=pk)
        except CertificatFormation.DoesNotExist:
            return Response({"detail": "Certificat introuvable"}, status=404)

        participant = getattr(request.user, "participant_dfir_profile", None)
        is_owner = participant is not None and certificat.inscription.participant_id == participant.id
        is_staff = hasattr(request.user, "profile") and DFIR_ENCADREMENT().has_permission(request, self)
        if not (is_owner or is_staff):
            return Response({"detail": "Accès refusé"}, status=403)

        pdf_bytes = self._render_pdf(certificat)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="certificat-{certificat.numero}.pdf"'
        return response

    def _render_pdf(self, certificat):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        c.setFillColorRGB(1, 0.51, 0)
        c.rect(0, height - 1.6 * cm, width, 1.6 * cm, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width / 2, height - 1.1 * cm, "LANEMA — Direction Formation, Innovation et Recherche")

        c.setFillColorRGB(0.12, 0.12, 0.12)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width / 2, height - 4.2 * cm, "Certificat de formation")

        c.setFont("Helvetica", 15)
        c.drawCentredString(width / 2, height - 6.2 * cm, "Ce certificat est délivré à")
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 7.6 * cm, str(certificat.inscription.participant))

        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 9.2 * cm, "pour avoir suivi avec succès la formation")
        c.setFont("Helvetica-Bold", 19)
        c.drawCentredString(width / 2, height - 10.4 * cm, certificat.inscription.session.formation.titre)

        c.setFont("Helvetica", 10)
        c.drawCentredString(
            width / 2, 2.3 * cm,
            f"N° {certificat.numero} — délivré le {certificat.date_delivrance.strftime('%d/%m/%Y')}",
        )
        c.drawCentredString(
            width / 2, 1.6 * cm,
            f"Vérifiable sur : {getattr(settings, 'FRONTEND_BASE_URL', '')}/dfir/verifier-certificat/{certificat.code_verification}",
        )

        c.showPage()
        c.save()
        return buffer.getvalue()


class CertificatVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, code):
        try:
            certificat = CertificatFormation.objects.select_related(
                "inscription__participant", "inscription__session__formation"
            ).get(code_verification=code)
        except (CertificatFormation.DoesNotExist, ValueError):
            return Response({"valide": False, "detail": "Certificat introuvable ou invalide."}, status=404)
        data = CertificatVerifySerializer(certificat).data
        data["valide"] = True
        return Response(data)
