from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_dashboard.mixins import log_historique_dae
from core.direction_access import direction_permission

from .models import Aeronef, ClientAeronautique, DemandeDAE, ReclamationClientDAE, SatisfactionDAE
from .serializers import (
    AeronefSerializer,
    ClientAeronautiqueSerializer,
    DemandeDAESerializer,
    ReclamationClientDAESerializer,
    SatisfactionDAEPublicSerializer,
    SatisfactionDAESerializer,
)

# Gestion des clients aéronautiques : réservée à l'encadrement DAE et plus
# (Admin/Directeur/Sous-Directeur/Chef d'atelier), ou à l'Agent administratif
# de palier terrain (cf. cahier des charges DAE section 29 : enregistre les
# clients, les demandes, prépare les dossiers).
DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')
DAE_CLIENTS = direction_permission('DAE', min_tier='encadrement', feature_key='dae_role_agent_administratif')

# Workflow de la reclamation client — cf. cahier des charges DAE section 22 :
# Enregistrement -> Analyse -> Affectation -> Traitement -> Reponse -> Cloture.
TRANSITIONS_RECLAMATION = {
    "ENREGISTREE": ["EN_ANALYSE"],
    "EN_ANALYSE": ["AFFECTEE"],
    "AFFECTEE": ["EN_TRAITEMENT"],
    "EN_TRAITEMENT": ["REPONSE_ENVOYEE"],
    "REPONSE_ENVOYEE": ["CLOTUREE"],
    "CLOTUREE": [],
}


def compute_clients_kpis(date_debut=None, date_fin=None):
    """Calcule les KPI clients de la DAE (categorie 5 + KPI 1 et 22 du cahier
    des charges section 24 : nombre de clients servis, taux de fidélisation).
    Reutilisable directement par le tableau de bord DAE."""
    from django.db.models import Count

    from aero_maintenance.models import OrdreTravail

    aeronefs = Aeronef.objects.all()
    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    clients_avec_ot = (
        ordres.filter(aeronef__client__isnull=False)
        .values("aeronef__client").annotate(nb=Count("id"))
    )
    nombre_clients_servis = clients_avec_ot.count()
    clients_fideles = sum(1 for c in clients_avec_ot if c["nb"] > 1)
    taux_fidelisation = (
        round(clients_fideles / nombre_clients_servis * 100, 1) if nombre_clients_servis else None
    )

    ordres_clotures = ordres.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"], date_fin__isnull=False)
    delai_moyen_restitution = None
    if ordres_clotures.exists():
        delais = [
            (o.date_fin - o.date_demande.date()).days for o in ordres_clotures
        ]
        delai_moyen_restitution = round(sum(delais) / len(delais), 1)

    reclamations = ReclamationClientDAE.objects.all()
    if date_debut and date_fin:
        reclamations = reclamations.filter(date_reception__range=(date_debut, date_fin))

    # Taux de satisfaction : moyenne combinee des fiches de satisfaction
    # post-intervention (5 criteres, cf. SatisfactionDAE) et des notes
    # laissees sur les reclamations traitees — deux sources, un seul taux.
    satisfactions = SatisfactionDAE.objects.filter(date_evaluation__isnull=False)
    notes_satisfaction = [s.note_moyenne for s in satisfactions if s.note_moyenne is not None]
    notes_reclamations = list(
        reclamations.filter(note_satisfaction__isnull=False).values_list("note_satisfaction", flat=True)
    )
    toutes_notes = notes_satisfaction + [float(n) for n in notes_reclamations]
    taux_satisfaction = round(sum(toutes_notes) / len(toutes_notes) / 5 * 100, 1) if toutes_notes else None

    reclamations_traitees = reclamations.filter(date_traitement__isnull=False)
    temps_moyen_traitement = None
    if reclamations_traitees.exists():
        delais_r = [(r.date_traitement - r.date_reception).days for r in reclamations_traitees]
        temps_moyen_traitement = round(sum(delais_r) / len(delais_r), 1)

    return {
        "nombre_clients_servis": nombre_clients_servis,
        "taux_fidelisation": taux_fidelisation,
        "nombre_aeronefs_pris_en_charge": aeronefs.count(),
        "nombre_ordres_travail_clotures": ordres_clotures.count(),
        "delai_moyen_restitution_jours": delai_moyen_restitution,
        "taux_satisfaction_clients": taux_satisfaction,
        "nombre_evaluations_satisfaction": satisfactions.count(),
        "nombre_reclamations": reclamations.count(),
        "temps_moyen_traitement_reclamations_jours": temps_moyen_traitement,
    }


class ClientAeronautiqueViewSet(viewsets.ModelViewSet):
    queryset = ClientAeronautique.objects.all()
    serializer_class = ClientAeronautiqueSerializer
    permission_classes = [DAE_CLIENTS]


class AeronefViewSet(viewsets.ModelViewSet):
    queryset = Aeronef.objects.select_related("client").all()
    serializer_class = AeronefSerializer
    permission_classes = [DAE_CLIENTS]


class ReclamationClientDAEViewSet(viewsets.ModelViewSet):
    queryset = ReclamationClientDAE.objects.select_related("client", "ordre_travail", "responsable").all()
    serializer_class = ReclamationClientDAESerializer
    permission_classes = [DAE_CLIENTS]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_historique_dae(instance, self.request.user, "Créée")

    @action(detail=True, methods=["post"], url_path="changer-statut")
    def changer_statut(self, request, pk=None):
        """Fait avancer la reclamation dans son cycle de vie (cf.
        TRANSITIONS_RECLAMATION). Verrous : l'affectation necessite un
        responsable deja renseigne, la reponse au client necessite un texte
        de reponse avant de pouvoir cloturer."""
        reclamation = self.get_object()
        nouveau_statut = request.data.get("statut")

        if nouveau_statut not in dict(ReclamationClientDAE.STATUT_CHOICES):
            return Response({"error": "Statut invalide."}, status=status.HTTP_400_BAD_REQUEST)
        transitions_valides = TRANSITIONS_RECLAMATION.get(reclamation.statut, [])
        if nouveau_statut not in transitions_valides:
            return Response(
                {"error": f"Transition {reclamation.statut} → {nouveau_statut} non autorisée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reclamation.statut == "EN_ANALYSE" and nouveau_statut == "AFFECTEE":
            analyse = request.data.get("analyse")
            responsable_id = request.data.get("responsable")
            if analyse:
                reclamation.analyse = analyse
            if responsable_id:
                reclamation.responsable_id = responsable_id
            if not reclamation.responsable_id:
                return Response(
                    {"error": "Un responsable doit être affecté avant de passer au traitement."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Cf. cahier des charges DAE section 28 — declencheur "réclamation" (affectation).
            from core.models import Notification

            Notification.objects.create(
                user_id=reclamation.responsable_id, type_notif="rappel",
                contenu=f"Réclamation {reclamation.reference} vous a été affectée",
                lien="/dae/clients",
            )

        if reclamation.statut == "EN_TRAITEMENT" and nouveau_statut == "REPONSE_ENVOYEE":
            reponse = request.data.get("reponse", "")
            if not reponse:
                return Response({"error": "La réponse au client est requise."}, status=status.HTTP_400_BAD_REQUEST)
            reclamation.reponse = reponse
            reclamation.date_reponse = timezone.now().date()

        ancien_statut = reclamation.statut
        reclamation.statut = nouveau_statut
        if nouveau_statut == "CLOTUREE":
            reclamation.date_traitement = timezone.now().date()
        reclamation.save()

        log_historique_dae(
            reclamation, request.user, "Statut modifié",
            ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut,
        )
        return Response(ReclamationClientDAESerializer(reclamation).data)


class SatisfactionDAEViewSet(viewsets.ModelViewSet):
    queryset = SatisfactionDAE.objects.select_related("ordre_travail__aeronef__client").all()
    serializer_class = SatisfactionDAESerializer
    permission_classes = [DAE_ENCADREMENT]

    @action(detail=False, methods=["post"], url_path="envoyer")
    def envoyer(self, request):
        """Cree (si besoin) la fiche de satisfaction pour un OT cloture et
        renvoie le lien — a transmettre manuellement ou par email au client."""
        from aero_maintenance.models import OrdreTravail

        ordre_travail_id = request.data.get("ordre_travail")
        try:
            ot = OrdreTravail.objects.select_related("aeronef__client").get(pk=ordre_travail_id)
        except OrdreTravail.DoesNotExist:
            return Response({"error": "Ordre de travail introuvable."}, status=404)
        if ot.statut not in ("TERMINE", "VALIDE", "CLOTURE"):
            return Response({"error": "L'OT doit être terminé avant d'envoyer la fiche de satisfaction."}, status=400)

        satisfaction, _created = SatisfactionDAE.objects.get_or_create(ordre_travail=ot)
        if satisfaction.date_evaluation is not None:
            return Response({"error": "Ce client a déjà soumis son évaluation."}, status=400)

        satisfaction.date_envoi = timezone.now()
        satisfaction.save(update_fields=["date_envoi"])

        lien = f"{getattr(settings, 'FRONTEND_BASE_URL', '')}/dae/satisfaction/{satisfaction.token}"
        client = ot.aeronef.client if ot.aeronef else None
        email = getattr(client, "email", "") if client else ""
        if email:
            send_mail(
                subject=f"Votre avis sur l'intervention {ot.reference}",
                message=(
                    f"Bonjour,\n\nMerci d'avoir fait confiance à la Direction de l'Aéronautique du LANEMA "
                    f"pour l'intervention {ot.reference}.\n"
                    "Votre avis nous aide à améliorer nos prestations : merci de prendre une minute pour l'évaluer.\n\n"
                    f"Lien vers la fiche de satisfaction : {lien}\n\nMerci pour votre confiance,\nDirection de l'Aéronautique — LANEMA"
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=True,
            )
        log_historique_dae(ot, request.user, "Fiche de satisfaction envoyée", nouvelle_valeur=lien)
        return Response({"lien": lien, "email_envoye": bool(email and "@" in email)})


class SatisfactionDAEPublicView(APIView):
    """Fiche de satisfaction publique : accessible via un lien unique (token)
    envoyé au client après clôture de l'OT, sans compte ni connexion."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_object(self, token):
        return SatisfactionDAE.objects.select_related("ordre_travail__aeronef__client").get(token=token)

    def get(self, request, token):
        try:
            satisfaction = self.get_object(token)
        except SatisfactionDAE.DoesNotExist:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SatisfactionDAEPublicSerializer(satisfaction).data)

    def post(self, request, token):
        try:
            satisfaction = self.get_object(token)
        except SatisfactionDAE.DoesNotExist:
            return Response({"detail": "Lien invalide."}, status=status.HTTP_404_NOT_FOUND)

        if satisfaction.date_evaluation is not None:
            return Response({"detail": "Cette évaluation a déjà été soumise."}, status=status.HTTP_400_BAD_REQUEST)

        criteres = ["note_qualite", "note_delai", "note_accueil", "note_communication", "note_prestation_technique"]
        notes = {}
        for critere in criteres:
            valeur = request.data.get(critere)
            try:
                valeur = int(valeur)
            except (TypeError, ValueError):
                return Response({"detail": "Merci de renseigner les 5 notes (sur 5)."}, status=status.HTTP_400_BAD_REQUEST)
            if not (1 <= valeur <= 5):
                return Response({"detail": "Les notes doivent être comprises entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)
            notes[critere] = valeur

        for critere, valeur in notes.items():
            setattr(satisfaction, critere, valeur)
        satisfaction.commentaire = request.data.get("commentaire", "")
        satisfaction.date_evaluation = timezone.now()
        satisfaction.save()

        return Response({"detail": "Merci pour votre évaluation !"})


class DemandeDAEViewSet(viewsets.ModelViewSet):
    queryset = DemandeDAE.objects.select_related("client", "aeronef", "ordre_travail").all()
    serializer_class = DemandeDAESerializer
    permission_classes = [DAE_CLIENTS]

    def perform_create(self, serializer):
        last_id = DemandeDAE.objects.count() + 1
        reference = f"DEM-DAE-{timezone.now().year}-{last_id:05d}"
        instance = serializer.save(reference=reference, cree_par=self.request.user)
        log_historique_dae(instance, self.request.user, "Créé")

    @action(detail=True, methods=["post"])
    def accepter(self, request, pk=None):
        """Cree l'Ordre de travail correspondant et le lie a la demande —
        seule etape de transformation Demande -> OT, cf. cahier des charges."""
        from aero_maintenance.models import OrdreTravail

        demande = self.get_object()
        if demande.statut in ("ACCEPTEE", "REFUSEE"):
            return Response(
                {"error": "Cette demande a déjà été traitée."}, status=status.HTTP_400_BAD_REQUEST
            )
        if demande.aeronef is None:
            return Response(
                {"error": "Un aéronef doit être renseigné avant d'accepter la demande."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_ot_id = OrdreTravail.objects.count() + 1
        ot = OrdreTravail.objects.create(
            reference=f"OT-DAE-{timezone.now().year}-{last_ot_id:05d}",
            aeronef=demande.aeronef,
            type_intervention=demande.type_intervention,
        )
        ancien_statut = demande.statut
        demande.ordre_travail = ot
        demande.statut = "ACCEPTEE"
        demande.date_traitement = timezone.now()
        demande.save(update_fields=["ordre_travail", "statut", "date_traitement"])
        log_historique_dae(
            demande, request.user, "Statut modifié",
            ancienne_valeur=ancien_statut, nouvelle_valeur=demande.statut,
        )
        log_historique_dae(ot, request.user, "Créé (depuis demande)", nouvelle_valeur=demande.reference)

        serializer = self.get_serializer(demande)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def refuser(self, request, pk=None):
        demande = self.get_object()
        if demande.statut in ("ACCEPTEE", "REFUSEE"):
            return Response(
                {"error": "Cette demande a déjà été traitée."}, status=status.HTTP_400_BAD_REQUEST
            )
        ancien_statut = demande.statut
        demande.statut = "REFUSEE"
        demande.date_traitement = timezone.now()
        demande.save(update_fields=["statut", "date_traitement"])
        log_historique_dae(
            demande, request.user, "Statut modifié",
            ancienne_valeur=ancien_statut, nouvelle_valeur=demande.statut,
        )

        serializer = self.get_serializer(demande)
        return Response(serializer.data)


class ClientsKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_clients_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
