from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_dashboard.mixins import HistoriqueMixin, log_historique_dae
from core.direction_access import direction_permission, has_dynamic_module_permission, scope_queryset_to_owner, user_tier
from core.pdf_utils import create_pdf_response

from .models import (
    BatterieAeronef,
    CertificatDAE,
    EquipementAeronautique,
    InspectionRoue,
    InterventionTechnique,
    OrdreTravail,
    RoueAeronef,
    TestBatterie,
)
from .pdf_utils import generate_certificat_ot_pdf

# Page "Maintenance" : seule page opérationnelle accessible au palier "terrain"
# (technicien) — mais un technicien ne voit/modifie que ses propres ordres de
# travail (scope_queryset_to_owner ci-dessous). Roues/Inspections/Batteries
# n'ont pas de "propriétaire" individuel : visibles à tout membre DAE.
DAE_MEMBRE = direction_permission('DAE')
from .serializers import (
    BatterieAeronefSerializer,
    EquipementAeronautiqueSerializer,
    InspectionRoueSerializer,
    InterventionTechniqueSerializer,
    OrdreTravailSerializer,
    RoueAeronefSerializer,
    TestBatterieSerializer,
)

# Chaque etape du journal InspectionRoue fait avancer RoueAeronef.statut (cf.
# cahier des charges section 8) — une non-conformite priori sur toute etape.
ROUE_STATUT_PAR_ETAPE = {
    "RECEPTION": "EN_INSPECTION",
    "IDENTIFICATION": "EN_INSPECTION",
    "DEMONTAGE": "EN_INSPECTION",
    "INSPECTION_PERIODIQUE": "EN_INSPECTION",
    "NETTOYAGE": "EN_INSPECTION",
    "REPARATION": "REPAREE",
    "REMPLACEMENT_COMPOSANT": "EN_INSPECTION",
    "REMONTAGE": "EN_INSPECTION",
    "EQUILIBRAGE": "EN_INSPECTION",
    "CONTROLE_FINAL": "EN_INSPECTION",
    "VALIDATION": "EN_SERVICE",
}

# Decision de test batterie -> statut (cf. cahier des charges section 9 :
# CONFORME / NON CONFORME / A REPARER / A REMPLACER).
BATTERIE_STATUT_PAR_RESULTAT = {
    "CONFORME": "EN_SERVICE",
    "NON_CONFORME": "HORS_SERVICE",
    "A_REPARER": "HORS_SERVICE",
    "A_REMPLACER": "HORS_SERVICE",
}

# Cycle de vie de l'OT (cf. cahier des charges DAE section 11) : chaque cle
# liste les transitions autorisees depuis ce statut. Le controle qualite est
# obligatoire avant de pouvoir passer de CONTROLE_QUALITE a TERMINE — cf.
# OrdreTravailViewSet.changer_statut, qui verifie qu'aucune non-conformite
# liee n'est encore ouverte.
TRANSITIONS_OT = {
    "A_PLANIFIER": ["PLANIFIE", "ANNULE"],
    "PLANIFIE": ["EN_COURS", "ANNULE"],
    "EN_COURS": ["EN_ATTENTE_PIECE", "EN_ATTENTE_CLIENT", "CONTROLE_QUALITE", "ANNULE"],
    "EN_ATTENTE_PIECE": ["EN_COURS", "ANNULE"],
    "EN_ATTENTE_CLIENT": ["EN_COURS", "ANNULE"],
    "CONTROLE_QUALITE": ["TERMINE", "EN_COURS"],
    "TERMINE": ["VALIDE"],
    "VALIDE": ["CLOTURE"],
    "CLOTURE": [],
    "ANNULE": [],
}

# Statuts "actifs" pour les besoins d'alerte/charge (un OT termine sa vie
# active des qu'il quitte le controle qualite avec succes).
STATUTS_NON_CLOS = ["A_PLANIFIER", "PLANIFIE", "EN_COURS", "EN_ATTENTE_PIECE", "EN_ATTENTE_CLIENT", "CONTROLE_QUALITE"]


def compute_maintenance_kpis(date_debut=None, date_fin=None):
    """Calcule les 10 KPI de maintenance (categorie 1) de la DAE. Reutilisable
    directement par le tableau de bord DAE."""
    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    termines = ordres.filter(statut__in=["TERMINE", "VALIDE", "CLOTURE"])

    prises_en_charge = ordres.filter(date_prise_charge__isnull=False)
    delais_prise_charge = [
        (o.date_prise_charge - o.date_demande).total_seconds() / 3600 for o in prises_en_charge
    ]
    temps_moyen_prise_en_charge = round(sum(delais_prise_charge) / len(delais_prise_charge), 1) if delais_prise_charge else None

    termines_avec_debut = termines.filter(date_debut__isnull=False, date_fin__isnull=False)
    mttr_list = [(o.date_fin - o.date_debut.date()).days for o in termines_avec_debut]
    mttr_jours = round(sum(mttr_list) / len(mttr_list), 1) if mttr_list else None

    termines_avec_prevue = termines.filter(date_fin_prevue__isnull=False, date_fin__isnull=False)
    ecarts_livraison = [(o.date_fin - o.date_fin_prevue).days for o in termines_avec_prevue]
    delai_moyen_livraison = round(sum(ecarts_livraison) / len(ecarts_livraison), 1) if ecarts_livraison else None

    nb_termines_avec_prevue = termines_avec_prevue.count()
    nb_dans_les_delais = sum(1 for o in termines_avec_prevue if o.date_fin <= o.date_fin_prevue)
    pct_travaux_dans_delais = (
        round(nb_dans_les_delais / nb_termines_avec_prevue * 100, 1) if nb_termines_avec_prevue else None
    )

    today = timezone.now().date()
    ordres_avec_prevue = ordres.filter(date_fin_prevue__isnull=False)
    nb_respectes = sum(
        1 for o in ordres_avec_prevue
        if (o.date_fin and o.date_fin <= o.date_fin_prevue) or (not o.date_fin and today <= o.date_fin_prevue)
    )
    taux_respect_delais = (
        round(nb_respectes / ordres_avec_prevue.count() * 100, 1) if ordres_avec_prevue.exists() else None
    )

    par_technicien = []
    techniciens_ids = ordres.filter(technicien__isnull=False).values_list("technicien", flat=True).distinct()
    for tech_id in techniciens_ids:
        ordres_tech = ordres.filter(technicien_id=tech_id)
        technicien = ordres_tech.first().technicien
        par_technicien.append({
            "technicien": technicien.get_full_name() or technicien.username,
            "nombre_interventions": ordres_tech.count(),
        })

    equipements = EquipementAeronautique.objects.all()
    if date_debut and date_fin:
        equipements = equipements.filter(date_reception__range=(date_debut, date_fin))

    return {
        "demandes_totales": ordres.count(),
        "preventives_realisees": termines.filter(type_intervention="PREVENTIVE").count(),
        "correctives_realisees": termines.filter(type_intervention="CORRECTIVE").count(),
        "urgences_realisees": termines.filter(type_intervention="URGENCE").count(),
        "temps_moyen_prise_en_charge_heures": temps_moyen_prise_en_charge,
        "mttr_jours": mttr_jours,
        "delai_moyen_livraison_jours": delai_moyen_livraison,
        "taux_respect_delais": taux_respect_delais,
        "pct_travaux_termines_dans_delais": pct_travaux_dans_delais,
        "interventions_par_technicien": par_technicien,
        "nombre_equipements_controles": equipements.count(),
    }


def compute_roues_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Roues d'aeronefs (categorie 2) de la DAE."""
    inspections = InspectionRoue.objects.all()
    if date_debut and date_fin:
        inspections = inspections.filter(date_inspection__range=(date_debut, date_fin))

    roues = RoueAeronef.objects.all()

    taux_conformite = (
        round(inspections.filter(conforme=True).count() / inspections.count() * 100, 1)
        if inspections.exists() else None
    )

    reparations = inspections.filter(type_inspection="REPARATION", ordre_travail__isnull=False)
    delais_reparation = []
    for insp in reparations.select_related("ordre_travail"):
        ot = insp.ordre_travail
        if ot.date_debut and ot.date_fin:
            delais_reparation.append((ot.date_fin - ot.date_debut.date()).days)
    temps_moyen_reparation = round(sum(delais_reparation) / len(delais_reparation), 1) if delais_reparation else None

    cycles = [r.nombre_cycles for r in roues]
    cycles_moyens = round(sum(cycles) / len(cycles), 1) if cycles else None

    return {
        "nombre_roues_inspectees": inspections.count(),
        "nombre_roues_reparees": roues.filter(statut="REPAREE").count(),
        "nombre_roues_remplacees": roues.filter(statut="REMPLACEE").count(),
        "nombre_roues_non_conformes": roues.filter(statut="NON_CONFORME").count(),
        "taux_conformite_roues": taux_conformite,
        "temps_moyen_reparation_jours": temps_moyen_reparation,
        "cycles_moyens": cycles_moyens,
        "nombre_inspections_periodiques": inspections.filter(type_inspection="INSPECTION_PERIODIQUE").count(),
    }


def compute_batteries_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Batteries d'aeronefs (categorie 3) de la DAE."""
    batteries = BatterieAeronef.objects.all()
    tests = TestBatterie.objects.all()
    if date_debut and date_fin:
        tests = tests.filter(date_test__date__range=(date_debut, date_fin))

    hors_service = batteries.filter(statut="HORS_SERVICE")

    taux_conformite = (
        round(tests.filter(resultat="CONFORME").count() / tests.count() * 100, 1) if tests.exists() else None
    )

    tests_avec_ot = tests.filter(ordre_travail__isnull=False).select_related("ordre_travail")
    durees_maintenance = [
        (t.ordre_travail.date_fin - t.ordre_travail.date_debut.date()).days
        for t in tests_avec_ot if t.ordre_travail.date_debut and t.ordre_travail.date_fin
    ]
    temps_moyen_maintenance = round(sum(durees_maintenance) / len(durees_maintenance), 1) if durees_maintenance else None

    fin_de_vie = hors_service.filter(date_mise_en_service__isnull=False, date_derniere_maintenance__isnull=False)
    durees_vie = [(b.date_derniere_maintenance - b.date_mise_en_service).days for b in fin_de_vie]
    duree_vie_moyenne = round(sum(durees_vie) / len(durees_vie), 1) if durees_vie else None

    return {
        "nombre_batteries_testees": tests.count(),
        "nombre_batteries_rechargees": batteries.filter(statut="RECHARGEE").count(),
        "nombre_batteries_reparees": batteries.filter(statut="REPAREE").count(),
        "nombre_batteries_remplacees": batteries.filter(statut="REMPLACEE").count(),
        "nombre_batteries_hors_service": hors_service.count(),
        "taux_conformite_batteries": taux_conformite,
        "temps_moyen_maintenance_jours": temps_moyen_maintenance,
        "duree_vie_moyenne_jours": duree_vie_moyenne,
    }


class OrdreTravailViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = OrdreTravail.objects.select_related("aeronef", "technicien", "piece_utilisee", "certificat").all()
    serializer_class = OrdreTravailSerializer
    permission_classes = [DAE_MEMBRE]

    def get_queryset(self):
        qs = scope_queryset_to_owner(super().get_queryset(), self.request, "technicien")
        # Filtrage optionnel par plage de dates — utilise par la page
        # Planification (Gantt) pour ne charger que la fenetre affichee,
        # sans dupliquer les donnees dans un nouveau modele de planning.
        date_debut = self.request.query_params.get("date_debut")
        date_fin = self.request.query_params.get("date_fin")
        if date_debut:
            qs = qs.filter(Q(date_fin_prevue__gte=date_debut) | Q(date_fin__gte=date_debut))
        if date_fin:
            qs = qs.filter(date_debut__date__lte=date_fin)
        return qs

    def perform_create(self, serializer):
        # Surcharge le perform_create du mixin (affectation auto du palier
        # terrain) — log quand meme dans l'historique, comme le ferait le mixin.
        from core.direction_access import user_tier
        if user_tier(self.request.user) == 'terrain' and not serializer.validated_data.get('technicien'):
            instance = serializer.save(technicien=self.request.user)
        else:
            instance = serializer.save()
        log_historique_dae(instance, self.request.user, "Créé")
    # perform_update herite de HistoriqueMixin (log les changements de statut).

    @action(detail=True, methods=["post"], url_path="changer-statut")
    def changer_statut(self, request, pk=None):
        """Fait avancer l'OT dans son cycle de vie, selon TRANSITIONS_OT.
        Verrou obligatoire : impossible de passer de Contrôle qualité à
        Terminé tant qu'une non-conformité liée à cet OT est encore ouverte
        (statut != CLOTUREE) — cf. cahier des charges section 16."""
        ordre_travail = self.get_object()
        nouveau_statut = request.data.get("statut")
        commentaire = request.data.get("commentaire", "")

        if nouveau_statut not in dict(OrdreTravail.STATUT_CHOICES):
            return Response({"error": "Statut invalide."}, status=status.HTTP_400_BAD_REQUEST)
        transitions_valides = TRANSITIONS_OT.get(ordre_travail.statut, [])
        if nouveau_statut not in transitions_valides:
            return Response(
                {"error": f"Transition {ordre_travail.statut} → {nouveau_statut} non autorisée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ordre_travail.statut == "CONTROLE_QUALITE" and nouveau_statut == "TERMINE":
            non_conformites_ouvertes = ordre_travail.non_conformites.exclude(statut="CLOTUREE")
            if non_conformites_ouvertes.exists():
                return Response(
                    {
                        "error": (
                            "Impossible de clôturer le contrôle qualité : "
                            f"{non_conformites_ouvertes.count()} non-conformité(s) encore ouverte(s) sur cet OT."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Separation des taches (cf. cahier des charges DAE section 29) :
            # le technicien assigne a l'OT ne peut pas valider lui-meme son
            # propre controle qualite — il faut l'encadrement ou un role
            # Controleur qualite dedie.
            if user_tier(request.user) == "terrain" and not has_dynamic_module_permission(
                request.user, "dae_role_controleur_qualite"
            ):
                return Response(
                    {"error": "Seul l'encadrement ou un contrôleur qualité peut valider le contrôle qualité."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        ancien_statut = ordre_travail.statut
        ordre_travail.statut = nouveau_statut
        if nouveau_statut == "EN_COURS" and not ordre_travail.date_debut:
            ordre_travail.date_debut = timezone.now()
        if nouveau_statut == "TERMINE" and not ordre_travail.date_fin:
            ordre_travail.date_fin = timezone.now().date()
        ordre_travail.save()

        log_historique_dae(
            ordre_travail, request.user, "Statut modifié",
            ancienne_valeur=ancien_statut, nouvelle_valeur=nouveau_statut,
        )
        if commentaire:
            log_historique_dae(ordre_travail, request.user, "Commentaire", nouvelle_valeur=commentaire)

        # Cf. cahier des charges DAE section 28 — declencheurs "changement de
        # statut", "validation" et "certificat disponible".
        from core.models import Notification

        from aero_dashboard.signals import _notifier_encadrement_dae

        if ordre_travail.technicien_id:
            Notification.objects.create(
                user=ordre_travail.technicien, type_notif="rappel",
                contenu=f"OT {ordre_travail.reference} : statut changé en « {ordre_travail.get_statut_display()} »",
                lien="/dae/maintenance",
            )
        if nouveau_statut == "VALIDE":
            _notifier_encadrement_dae("rappel", f"OT {ordre_travail.reference} validé", lien="/dae/maintenance")
        elif nouveau_statut == "TERMINE":
            _notifier_encadrement_dae(
                "rappel", f"Certificat disponible pour l'OT {ordre_travail.reference}", lien="/dae/maintenance"
            )

        return Response(OrdreTravailSerializer(ordre_travail).data)

    @action(detail=True, methods=["get"], url_path="telecharger-certificat")
    def telecharger_certificat(self, request, pk=None):
        ordre_travail = self.get_object()
        if ordre_travail.statut not in ("TERMINE", "VALIDE", "CLOTURE"):
            return Response(
                {"error": "Le certificat n'est disponible qu'après le contrôle qualité (Terminé, Validé ou Clôturé)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        certificat, _ = CertificatDAE.objects.get_or_create(ordre_travail=ordre_travail)
        buffer = generate_certificat_ot_pdf(ordre_travail, numero_certificat=certificat.numero)
        return create_pdf_response(buffer, f"{certificat.numero}.pdf")


class InterventionTechniqueViewSet(viewsets.ModelViewSet):
    """Journal d'intervention technique — un technicien ne voit/modifie que
    les entrées liées à ses propres ordres de travail (palier terrain)."""

    queryset = InterventionTechnique.objects.select_related("ordre_travail", "technicien").prefetch_related("pieces_utilisees").all()
    serializer_class = InterventionTechniqueSerializer
    permission_classes = [DAE_MEMBRE]

    def get_queryset(self):
        qs = scope_queryset_to_owner(super().get_queryset(), self.request, "ordre_travail__technicien")
        ordre_travail = self.request.query_params.get("ordre_travail")
        if ordre_travail:
            qs = qs.filter(ordre_travail_id=ordre_travail)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(technicien=self.request.user)
        # Consommation automatique du stock a partir des pieces reellement
        # utilisees pendant l'intervention (cf. cahier des charges section
        # 32 : donnees calculees depuis les operations, pas saisies a part).
        from aero_stock.models import MouvementPieceRechange

        for piece in instance.pieces_utilisees.all():
            MouvementPieceRechange.objects.create(piece=piece, type_mouvement="SORTIE", quantite=1)
            piece.quantite_stock = max(0, piece.quantite_stock - 1)
            piece.save(update_fields=["quantite_stock"])
        log_historique_dae(
            instance.ordre_travail, self.request.user, "Intervention ajoutée",
            nouvelle_valeur=f"{instance.get_operation_display()} ({instance.temps_passe_minutes} min)",
        )


class EquipementAeronautiqueViewSet(HistoriqueMixin, viewsets.ModelViewSet):
    queryset = EquipementAeronautique.objects.select_related("aeronef").all()
    serializer_class = EquipementAeronautiqueSerializer
    permission_classes = [DAE_MEMBRE]


class RoueAeronefViewSet(viewsets.ModelViewSet):
    queryset = RoueAeronef.objects.select_related("aeronef").all()
    serializer_class = RoueAeronefSerializer
    permission_classes = [DAE_MEMBRE]


class InspectionRoueViewSet(viewsets.ModelViewSet):
    queryset = InspectionRoue.objects.select_related("roue", "ordre_travail", "technicien").all()
    serializer_class = InspectionRoueSerializer
    permission_classes = [DAE_MEMBRE]

    def get_queryset(self):
        qs = super().get_queryset()
        roue = self.request.query_params.get("roue")
        if roue:
            qs = qs.filter(roue_id=roue)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(technicien=self.request.user)
        roue = instance.roue
        nouveau_statut = "NON_CONFORME" if not instance.conforme else ROUE_STATUT_PAR_ETAPE.get(instance.type_inspection, roue.statut)
        roue.statut = nouveau_statut
        roue.date_derniere_intervention = timezone.now().date()
        roue.save(update_fields=["statut", "date_derniere_intervention"])
        log_historique_dae(
            roue, self.request.user, "Étape de traitement",
            nouvelle_valeur=f"{instance.get_type_inspection_display()} ({'conforme' if instance.conforme else 'non conforme'})",
        )


class BatterieAeronefViewSet(viewsets.ModelViewSet):
    queryset = BatterieAeronef.objects.select_related("aeronef").all()
    serializer_class = BatterieAeronefSerializer
    permission_classes = [DAE_MEMBRE]


class TestBatterieViewSet(viewsets.ModelViewSet):
    queryset = TestBatterie.objects.select_related("batterie", "ordre_travail", "technicien").all()
    serializer_class = TestBatterieSerializer
    permission_classes = [DAE_MEMBRE]

    def get_queryset(self):
        qs = super().get_queryset()
        batterie = self.request.query_params.get("batterie")
        if batterie:
            qs = qs.filter(batterie_id=batterie)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(technicien=self.request.user)
        batterie = instance.batterie
        batterie.statut = BATTERIE_STATUT_PAR_RESULTAT.get(instance.resultat, batterie.statut)
        batterie.date_derniere_maintenance = timezone.now().date()
        batterie.save(update_fields=["statut", "date_derniere_maintenance"])
        log_historique_dae(
            batterie, self.request.user, "Test batterie",
            nouvelle_valeur=f"{instance.get_resultat_display()}",
        )


class MaintenanceKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_maintenance_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class RouesKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_roues_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class BatteriesKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_batteries_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
