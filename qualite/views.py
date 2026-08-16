from django.db.models import Count, F
from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActionQualite, Audit, Echantillon, Essai, NonConformite, RecommandationAudit
from .serializers import (
    ActionQualiteSerializer,
    AuditSerializer,
    EchantillonSerializer,
    EssaiSerializer,
    NonConformiteSerializer,
    RecommandationAuditSerializer,
)
from clients.permissions_catalog import user_has_permission


class EchantillonViewSet(viewsets.ModelViewSet):
    queryset = Echantillon.objects.select_related('demande', 'demande__facture').all()
    serializer_class = EchantillonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        statut = self.request.query_params.get('statut')
        if statut and statut != 'TOUS':
            queryset = queryset.filter(statut=statut)
        role = getattr(getattr(self.request.user, "client_profile", None), "role", None)
        if role == "CLIENT":
            queryset = queryset.filter(demande__client=self.request.user)
        return queryset

    def _check_labo_staff(self):
        if not user_has_permission(self.request.user, "echantillons.manage"):
            raise PermissionDenied("Seul le personnel du laboratoire peut gérer les échantillons.")

    def perform_create(self, serializer):
        self._check_labo_staff()
        demande = serializer.validated_data.get("demande")
        if demande is not None and (demande.facture is None or demande.facture.statut != "PAYEE"):
            raise ValidationError(
                {"detail": "Le paiement doit être validé avant la réception des échantillons."}
            )
        serializer.save()

    def perform_update(self, serializer):
        self._check_labo_staff()
        serializer.save()

    def perform_destroy(self, instance):
        self._check_labo_staff()
        instance.delete()


class NonConformiteViewSet(viewsets.ModelViewSet):
    queryset = NonConformite.objects.all().order_by("-date_creation")
    serializer_class = NonConformiteSerializer
    permission_classes = [permissions.IsAuthenticated]


class AuditViewSet(viewsets.ModelViewSet):
    queryset = Audit.objects.all().order_by("-date_audit")
    serializer_class = AuditSerializer
    permission_classes = [permissions.IsAuthenticated]


class EssaiViewSet(viewsets.ModelViewSet):
    queryset = Essai.objects.select_related('echantillon').all()
    serializer_class = EssaiSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        statut = self.request.query_params.get('statut')
        if statut and statut != 'TOUS':
            queryset = queryset.filter(statut=statut)
        return queryset


class QualiteDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ncs = NonConformite.objects.all()
        data = {
            "total_non_conformites": ncs.count(),
            "majeures": ncs.filter(gravite="MAJEURE").count(),
            "critiques": ncs.filter(gravite="CRITIQUE").count(),
            "par_type": list(
                NonConformite.objects.values("type_nc").annotate(total=Count("id"))
            ),
            "nb_audits": Audit.objects.count(),
        }
        return Response(data)


# ============================================================
# KPI decisionnels DEA (module laboratoire)
# ============================================================

def compute_echantillons_kpis(date_debut=None, date_fin=None):
    """Calcule les 9 KPI de gestion des echantillons."""
    echantillons = Echantillon.objects.all()
    recus = echantillons
    enregistres = echantillons
    if date_debut and date_fin:
        recus = echantillons.filter(date_reception__range=(date_debut, date_fin))
        enregistres = echantillons.filter(created_at__date__range=(date_debut, date_fin))

    nb_conformes = echantillons.filter(conforme=True).count()
    nb_non_conformes = echantillons.filter(conforme=False).count()
    total_evalues = nb_conformes + nb_non_conformes
    taux_conformite = round(nb_conformes / total_evalues * 100, 1) if total_evalues else None

    return {
        "nombre_echantillons_recus": recus.count(),
        "nombre_echantillons_enregistres": enregistres.count(),
        "nombre_echantillons_en_attente": echantillons.filter(statut="EN_ATTENTE").count(),
        "nombre_echantillons_en_cours_analyse": echantillons.filter(statut="EN_ANALYSE").count(),
        "nombre_echantillons_analyses": echantillons.filter(statut__in=["TERMINE", "ARCHIVE"]).count(),
        "nombre_echantillons_rejetes": echantillons.filter(statut="REJETE").count(),
        "nombre_echantillons_non_conformes": nb_non_conformes,
        "nombre_echantillons_conformes": nb_conformes,
        "taux_conformite_echantillons": taux_conformite,
    }


def compute_essais_kpis(date_debut=None, date_fin=None):
    """Calcule les 9 KPI des essais et analyses."""
    essais = Essai.objects.all()
    if date_debut and date_fin:
        essais = essais.filter(created_at__date__range=(date_debut, date_fin))

    realises = essais.filter(statut__in=["TERMINE", "VALIDE"])
    non_annules = essais.exclude(statut="ANNULE")

    par_laboratoire = list(
        essais.exclude(laboratoire__isnull=True)
        .values("laboratoire__nom")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    par_type = list(
        essais.exclude(type_essai="")
        .values("type_essai")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    nb_valides = essais.filter(statut="VALIDE").count()
    taux_reussite = round(nb_valides / non_annules.count() * 100, 1) if non_annules.count() else None

    nb_reprises = essais.filter(est_reprise=True).count()
    taux_reprise = round(nb_reprises / essais.count() * 100, 1) if essais.count() else None

    essais_avec_dates = essais.filter(date_fin__isnull=False, date_fin_prevue__isnull=False)
    nb_dans_les_delais = essais_avec_dates.filter(date_fin__lte=F("date_fin_prevue")).count()
    respect_delais = (
        round(nb_dans_les_delais / essais_avec_dates.count() * 100, 1) if essais_avec_dates.count() else None
    )

    nb_laboratoires = essais.exclude(laboratoire__isnull=True).values("laboratoire").distinct().count()
    productivite_laboratoires = round(realises.count() / nb_laboratoires, 2) if nb_laboratoires else None

    return {
        "nombre_total_essais_realises": realises.count(),
        "nombre_essais_par_laboratoire": par_laboratoire,
        "nombre_essais_par_type": par_type,
        "taux_reussite_essais": taux_reussite,
        "taux_reprise_essais": taux_reprise,
        "nombre_essais_annules": essais.filter(statut="ANNULE").count(),
        "nombre_essais_urgents_realises": essais.filter(urgent=True, statut__in=["TERMINE", "VALIDE"]).count(),
        "respect_delais_analyse": respect_delais,
        "productivite_laboratoires": productivite_laboratoires,
    }


def compute_techniciens_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI des techniciens et analystes."""
    essais = Essai.objects.all()
    if date_debut and date_fin:
        essais = essais.filter(created_at__date__range=(date_debut, date_fin))

    essais_avec_tech = essais.exclude(technicien_user__isnull=True)

    par_technicien = []
    for tech_id in essais_avec_tech.values_list("technicien_user", flat=True).distinct():
        essais_tech = essais_avec_tech.filter(technicien_user_id=tech_id)
        realises_tech = essais_tech.filter(statut__in=["TERMINE", "VALIDE"])
        duree = essais_tech.filter(date_debut__isnull=False, date_fin__isnull=False)
        temps_moyen = None
        if duree.exists():
            durees = [(e.date_fin - e.date_debut).days for e in duree]
            temps_moyen = round(sum(durees) / len(durees), 1)
        nb_erreurs = essais_tech.filter(erreur_detectee=True).count()
        nb_reprises = essais_tech.filter(est_reprise=True).count()
        total_tech = essais_tech.count()
        par_technicien.append({
            "technicien": essais_tech.first().technicien_user.username,
            "nombre_analyses_realisees": realises_tech.count(),
            "temps_moyen_par_analyse_jours": temps_moyen,
            "nombre_erreurs_detectees": nb_erreurs,
            "nombre_reprises": nb_reprises,
            "taux_qualite": round((1 - nb_erreurs / total_tech) * 100, 1) if total_tech else None,
            "charge_travail_en_cours": essais_tech.filter(statut="EN_COURS").count(),
        })

    total_essais_tech = essais_avec_tech.count()
    nb_erreurs_total = essais_avec_tech.filter(erreur_detectee=True).count()
    nb_reprises_total = essais_avec_tech.filter(est_reprise=True).count()
    nb_non_conformites_liees = NonConformite.objects.filter(essai__in=essais_avec_tech).count()

    return {
        "par_technicien": par_technicien,
        "nombre_erreurs_detectees_total": nb_erreurs_total,
        "nombre_reprises_total": nb_reprises_total,
        "taux_productivite": round(
            essais_avec_tech.filter(statut__in=["TERMINE", "VALIDE"]).count() / total_essais_tech * 100, 1
        ) if total_essais_tech else None,
        "taux_qualite_global": round((1 - nb_erreurs_total / total_essais_tech) * 100, 1) if total_essais_tech else None,
        "taux_respect_procedures": round(
            (1 - nb_non_conformites_liees / total_essais_tech) * 100, 1
        ) if total_essais_tech else None,
    }


def compute_qualite_iso_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI qualite ISO/IEC 17025 (module labo)."""
    from core.models import Document

    non_conformites = NonConformite.objects.all()
    if date_debut and date_fin:
        non_conformites = non_conformites.filter(date_creation__range=(date_debut, date_fin))

    actions = ActionQualite.objects.all()
    nb_correctives = actions.filter(type="CORRECTIVE").count()
    nb_preventives = actions.filter(type="PREVENTIVE").count()
    nb_actions_total = actions.count()
    nb_actions_cloturees = actions.filter(statut="CLOTUREE").count()
    taux_cloture = round(nb_actions_cloturees / nb_actions_total * 100, 1) if nb_actions_total else None

    audits = Audit.objects.all()
    audits_avec_resultat = audits.exclude(resultat="")
    nb_conformes = audits_avec_resultat.filter(resultat__icontains="conforme").exclude(
        resultat__icontains="non"
    ).count()
    taux_conformite_procedures = (
        round(nb_conformes / audits_avec_resultat.count() * 100, 1) if audits_avec_resultat.count() else None
    )

    recommandations = RecommandationAudit.objects.all()
    nb_recommandations_appliquees = recommandations.filter(appliquee=True).count()

    documents_qualite = Document.objects.filter(categorie__nom__icontains="qualit")
    taux_conformite_documentaire = None
    note_documentaire = None
    if documents_qualite.exists():
        nb_valides = documents_qualite.exclude(statut="brouillon").count()
        taux_conformite_documentaire = round(nb_valides / documents_qualite.count() * 100, 1)
    else:
        note_documentaire = (
            "Aucune categorie GED 'qualite' identifiee : indicateur non calculable en l'etat."
        )

    return {
        "nombre_non_conformites": non_conformites.count(),
        "nombre_actions_correctives": nb_correctives,
        "nombre_actions_preventives": nb_preventives,
        "taux_cloture_actions": taux_cloture,
        "nombre_audits_realises": audits.count(),
        "nombre_recommandations_appliquees": nb_recommandations_appliquees,
        "taux_conformite_documentaire": taux_conformite_documentaire,
        "taux_conformite_documentaire_note": note_documentaire,
        "taux_conformite_procedures": taux_conformite_procedures,
    }


class ActionQualiteViewSet(viewsets.ModelViewSet):
    queryset = ActionQualite.objects.select_related("non_conformite", "responsable").all()
    serializer_class = ActionQualiteSerializer
    permission_classes = [permissions.IsAuthenticated]


class RecommandationAuditViewSet(viewsets.ModelViewSet):
    queryset = RecommandationAudit.objects.select_related("audit").all()
    serializer_class = RecommandationAuditSerializer
    permission_classes = [permissions.IsAuthenticated]


class EchantillonsKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_echantillons_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class EssaisKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_essais_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class TechniciensKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_techniciens_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class QualiteIsoKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_qualite_iso_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
