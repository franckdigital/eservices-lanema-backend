"""
Module GED — Gestion Électronique des Documents & Archivage central, couvrant
courrier/diligence/réunion/tâche (liens historiques) ainsi que, via
rattachement générique (content_type/object_id), n'importe quel enregistrement
métier (patrimoine, comptabilité, finance, moyens généraux, facturation/
recouvrement, labo...). L'administration de l'archive (catégories, corbeille,
destruction, vue d'ensemble) est réservée au Service Information & Documentation,
à la Direction Générale et à Admin ; le rattachement de ses propres documents
reste ouvert à tout compte authentifié, comme aujourd'hui.
"""
import hashlib
from datetime import date, timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import permissions, viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, is_full_access_user, user_direction_code

from .models import (
    CategorieDocument, Document, DocumentVersion,
    DocumentAccess, DocumentLog, CertificatArchivage,
    DocumentShareLink, DemandeDestruction,
)
from .ged_serializers import (
    CategorieDocumentSerializer, DocumentListSerializer,
    DocumentDetailSerializer, DocumentVersionSerializer,
    DocumentAccessSerializer, DocumentLogSerializer,
    CertificatArchivageSerializer, DocumentShareLinkSerializer,
    DemandeDestructionSerializer,
)
from .ocr_utils import extraire_texte_document

DG_GED_MEMBRE = direction_permission('DG_GED')


def _is_ged_admin(user):
    """Service Information & Documentation, Direction Générale, ou Admin :
    voit et administre l'intégralité de l'archive GED, tous modules confondus."""
    if is_full_access_user(user):
        return True
    return user_direction_code(user) == 'DG_GED'


class IsGedAdminOrReadOnly(permissions.BasePermission):
    """Lecture ouverte à tout compte authentifié (ex: choisir une catégorie
    pour classer son propre courrier) ; création/modification/suppression des
    catégories réservée aux administrateurs de l'archive."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_ged_admin(request.user)


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log(document, user, action, details='', request=None):
    DocumentLog.objects.create(
        document=document,
        utilisateur=user,
        action=action,
        details=details,
        adresse_ip=_get_client_ip(request) if request else None,
    )


def _extraire_et_sauver_texte(document):
    """Extrait le texte du fichier (PDF) et le sauvegarde dans contenu_ocr,
    pour alimenter la recherche plein texte — best-effort, ne bloque jamais
    la sauvegarde du document en cas d'échec."""
    try:
        texte = extraire_texte_document(document.fichier)
        if texte and texte != document.contenu_ocr:
            document.contenu_ocr = texte
            document.save(update_fields=['contenu_ocr'])
    except Exception:
        pass


def _peut_acceder(user, document):
    """Vérifie si l'utilisateur peut accéder au document selon son rôle et les droits explicites."""
    if _is_ged_admin(user):
        return True
    profile = getattr(user, 'profile', None)
    role = getattr(profile, 'role', None)

    if role == 'ADMIN':
        return True
    if document.auteur == user:
        return True
    if document.confidentialite == 'public':
        return True
    if document.confidentialite == 'interne':
        # Même service ou accès explicite
        if profile and profile.service and document.service == profile.service:
            return True
    # Accès explicite
    if DocumentAccess.objects.filter(document=document, user=user).exists():
        return True
    # Directeur voit les documents de sa direction
    if role in ('DIRECTEUR', 'SOUS_DIRECTEUR') and profile and profile.service:
        if document.service and document.service.sous_direction == profile.service.sous_direction:
            return True
    return False


class CategorieDocumentViewSet(viewsets.ModelViewSet):
    queryset = CategorieDocument.objects.filter(parent__isnull=True)
    serializer_class = CategorieDocumentSerializer
    permission_classes = [IsGedAdminOrReadOnly]

    @action(detail=False, methods=['get'])
    def arborescence(self, request):
        """Retourne l'arborescence complète des catégories."""
        categories = CategorieDocument.objects.filter(parent__isnull=True)
        return Response(CategorieDocumentSerializer(categories, many=True).data)


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titre', 'reference', 'mots_cles', 'contenu_ocr', 'description']
    ordering_fields = ['created_at', 'date_document', 'titre', 'statut']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('list', 'mes_documents', 'recherche'):
            return DocumentListSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        role = getattr(profile, 'role', None)

        if self.action == 'corbeille':
            base = Document.objects.filter(est_supprime=True)
            qs = base if _is_ged_admin(user) else base.filter(auteur=user)
            return qs.distinct()

        if _is_ged_admin(user) or role == 'ADMIN':
            # Vue d'ensemble complète : Service Information & Documentation,
            # Direction Générale et Admin voient toute l'archive, tous
            # modules confondus (courrier/diligence/... + rattachements
            # génériques patrimoine/comptabilité/finance/...).
            qs = Document.objects.filter(est_supprime=False)
        elif role in ('DIRECTEUR', 'SOUS_DIRECTEUR'):
            qs = Document.objects.filter(
                Q(auteur=user) |
                Q(confidentialite__in=['public', 'interne']) |
                Q(acces__user=user),
                est_supprime=False,
            )
        else:
            qs = Document.objects.filter(
                Q(auteur=user) |
                Q(confidentialite='public') |
                Q(acces__user=user) |
                Q(confidentialite='interne', service=profile.service if profile else None),
                est_supprime=False,
            )

        # Filtres optionnels
        params = self.request.query_params
        if params.get('statut'):
            qs = qs.filter(statut=params['statut'])
        if params.get('categorie'):
            qs = qs.filter(categorie_id=params['categorie'])
        if params.get('confidentialite'):
            qs = qs.filter(confidentialite=params['confidentialite'])
        if params.get('service'):
            qs = qs.filter(service_id=params['service'])
        if params.get('type_fichier'):
            qs = qs.filter(type_fichier=params['type_fichier'])
        if params.get('date_debut'):
            qs = qs.filter(date_document__gte=params['date_debut'])
        if params.get('date_fin'):
            qs = qs.filter(date_document__lte=params['date_fin'])
        if params.get('auteur'):
            qs = qs.filter(auteur_id=params['auteur'])
        if params.get('diligence'):
            qs = qs.filter(diligence_id=params['diligence'])
        if params.get('courrier'):
            qs = qs.filter(courrier_id=params['courrier'])
        if params.get('app_label') and params.get('model'):
            try:
                ct = ContentType.objects.get(app_label=params['app_label'], model=params['model'])
                qs = qs.filter(content_type=ct, object_id=params.get('object_id'))
            except ContentType.DoesNotExist:
                qs = qs.none()

        return qs.distinct()

    def perform_create(self, serializer):
        doc = serializer.save(auteur=self.request.user)
        _log(doc, self.request.user, 'creation', request=self.request)
        _extraire_et_sauver_texte(doc)

    def destroy(self, request, *args, **kwargs):
        """Suppression douce : envoie à la corbeille plutôt que de supprimer
        définitivement (récupérable via /restaurer/)."""
        doc = self.get_object()
        doc.est_supprime = True
        doc.supprime_le = timezone.now()
        doc.supprime_par = request.user
        doc.save(update_fields=['est_supprime', 'supprime_le', 'supprime_par'])
        _log(doc, request.user, 'suppression', request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---- CORBEILLE ----

    @action(detail=False, methods=['get'])
    def corbeille(self, request):
        qs = self.get_queryset()
        return Response(DocumentListSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def restaurer(self, request, pk=None):
        doc = Document.objects.get(pk=pk)
        if not (doc.auteur == request.user or _is_ged_admin(request.user)):
            return Response({'detail': 'Accès refusé.'}, status=403)
        doc.est_supprime = False
        doc.supprime_le = None
        doc.supprime_par = None
        doc.save(update_fields=['est_supprime', 'supprime_le', 'supprime_par'])
        _log(doc, request.user, 'restauration', request=request)
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def supprimer_definitivement(self, request, pk=None):
        """Suppression irréversible depuis la corbeille — réservée aux
        administrateurs de l'archive."""
        if not _is_ged_admin(request.user):
            return Response({'detail': 'Accès refusé.'}, status=403)
        doc = Document.objects.get(pk=pk)
        if not doc.est_supprime:
            return Response({'error': "Le document doit d'abord être envoyé à la corbeille."}, status=400)
        doc.delete()
        return Response(status=204)

    # ---- RATTACHEMENT GÉNÉRIQUE (patrimoine, comptabilité, finance, moyens
    # généraux, facturation/recouvrement, labo...) ----

    @action(detail=False, methods=['post'])
    def attacher(self, request):
        """Téléverse un document et le rattache à n'importe quel enregistrement
        métier via (app_label, model, object_id) — ex: un Bien patrimonial,
        une pièce comptable, une facture."""
        app_label = request.data.get('app_label')
        model_name = request.data.get('model')
        object_id = request.data.get('object_id')
        fichier = request.FILES.get('fichier')
        if not (app_label and model_name and object_id and fichier):
            return Response({'error': 'app_label, model, object_id et fichier sont requis.'}, status=400)
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            return Response({'error': 'Type d\'objet inconnu.'}, status=400)

        doc = Document.objects.create(
            titre=request.data.get('titre') or fichier.name,
            description=request.data.get('description', ''),
            categorie_id=request.data.get('categorie') or None,
            fichier=fichier,
            type_fichier=request.data.get('type_fichier', 'autre'),
            confidentialite=request.data.get('confidentialite', 'interne'),
            date_document=request.data.get('date_document') or None,
            auteur=request.user,
            service=getattr(getattr(request.user, 'profile', None), 'service', None),
            content_type=ct,
            object_id=object_id,
        )
        _log(doc, request.user, 'creation', details=f"Rattaché à {app_label}.{model_name}#{object_id}", request=request)
        _extraire_et_sauver_texte(doc)
        return Response(DocumentDetailSerializer(doc).data, status=201)

    @action(detail=False, methods=['get'])
    def documents_pour_objet(self, request):
        """Liste les documents GED rattachés à un enregistrement métier donné
        (?app_label=dg_patrimoine&model=bien&object_id=12)."""
        app_label = request.query_params.get('app_label')
        model_name = request.query_params.get('model')
        object_id = request.query_params.get('object_id')
        if not (app_label and model_name and object_id):
            return Response({'error': 'app_label, model et object_id sont requis.'}, status=400)
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            return Response([], status=200)
        qs = self.get_queryset().filter(content_type=ct, object_id=object_id)
        return Response(DocumentListSerializer(qs, many=True).data)

    # ---- RECHERCHE PLEIN TEXTE / EXTRACTION ----

    @action(detail=True, methods=['post'])
    def extraire_texte(self, request, pk=None):
        """(Ré)extrait le texte du fichier (PDF) pour la recherche plein texte."""
        doc = self.get_object()
        texte = extraire_texte_document(doc.fichier)
        doc.contenu_ocr = texte
        doc.save(update_fields=['contenu_ocr'])
        _log(doc, request.user, 'extraction_texte',
             details=f"{len(texte)} caractères extraits" if texte else "Aucun texte extrait", request=request)
        return Response({'contenu_ocr': texte, 'longueur': len(texte)})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not _peut_acceder(request.user, instance):
            _log(instance, request.user, 'acces_refuse', request=request)
            return Response({'detail': 'Accès refusé.'}, status=status.HTTP_403_FORBIDDEN)
        _log(instance, request.user, 'consultation', request=request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ---- RECHERCHE PLEIN TEXTE ----

    @action(detail=False, methods=['get'])
    def recherche(self, request):
        """
        Recherche multicritère et plein texte.
        ?q=mot_cle&categorie=1&statut=valide&date_debut=&date_fin=&auteur=
        """
        q = request.query_params.get('q', '').strip()
        qs = self.get_queryset()
        if q:
            qs = qs.filter(
                Q(titre__icontains=q) |
                Q(reference__icontains=q) |
                Q(description__icontains=q) |
                Q(mots_cles__icontains=q) |
                Q(contenu_ocr__icontains=q)
            )
        return Response(DocumentListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def mes_documents(self, request):
        qs = Document.objects.filter(auteur=request.user).order_by('-created_at')
        return Response(DocumentListSerializer(qs, many=True).data)

    # ---- WORKFLOW ----

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """Change le statut du document dans son cycle de vie."""
        doc = self.get_object()
        nouveau_statut = request.data.get('statut')
        commentaire = request.data.get('commentaire', '')

        transitions_valides = {
            'brouillon': ['en_validation'],
            'en_validation': ['valide', 'brouillon'],
            'valide': ['signe', 'diffuse'],
            'signe': ['diffuse'],
            'diffuse': ['archive'],
            'archive': [],
        }

        if nouveau_statut not in dict(Document.STATUT_CHOICES):
            return Response({'error': 'Statut invalide.'}, status=400)
        if nouveau_statut not in transitions_valides.get(doc.statut, []):
            return Response(
                {'error': f"Transition {doc.statut} → {nouveau_statut} non autorisée."},
                status=400
            )

        doc.statut = nouveau_statut
        if nouveau_statut == 'archive':
            doc.archive_le = timezone.now()
            doc.archive_par = request.user
        doc.save()
        _log(doc, request.user, 'modification',
             details=f"Statut → {nouveau_statut}. {commentaire}", request=request)
        return Response(DocumentDetailSerializer(doc).data)

    # ---- ARCHIVAGE LÉGAL ----

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        """Archive légalement le document et génère un certificat SHA256."""
        doc = self.get_object()
        if doc.statut == 'archive':
            return Response({'error': 'Document déjà archivé.'}, status=400)

        # Calcul durée conservation
        duree = request.data.get('duree_conservation_ans')
        if not duree and doc.categorie:
            duree = doc.categorie.duree_conservation_ans
        duree = int(duree) if duree else 10

        doc.statut = 'archive'
        doc.archive_le = timezone.now()
        doc.archive_par = request.user
        doc.duree_conservation_ans = duree
        doc.date_destruction_prevue = date.today().replace(year=date.today().year + duree)
        doc.save()

        # Génère le certificat
        from django.utils.crypto import get_random_string
        numero = f"CERT-{timezone.now().year}-{get_random_string(8).upper()}"
        CertificatArchivage.objects.get_or_create(
            document=doc,
            defaults={
                'numero_certificat': numero,
                'hash_sha256': doc.hash_sha256,
                'auteur': request.user,
                'metadata': {
                    'titre': doc.titre,
                    'reference': doc.reference,
                    'archive_le': doc.archive_le.isoformat(),
                    'duree_conservation_ans': duree,
                    'date_destruction_prevue': str(doc.date_destruction_prevue),
                }
            }
        )
        _log(doc, request.user, 'archivage', request=request)
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['get'])
    def certificat(self, request, pk=None):
        """Retourne le certificat d'archivage du document."""
        doc = self.get_object()
        try:
            cert = doc.certificat_archivage
        except CertificatArchivage.DoesNotExist:
            return Response({'detail': 'Aucun certificat pour ce document.'}, status=404)
        return Response(CertificatArchivageSerializer(cert).data)

    @action(detail=True, methods=['get'])
    def verifier_integrite(self, request, pk=None):
        """Vérifie que le fichier n'a pas été altéré depuis l'archivage."""
        doc = self.get_object()
        if not doc.hash_sha256:
            return Response({'valide': False, 'message': 'Aucun hash enregistré.'})
        try:
            sha256 = hashlib.sha256()
            doc.fichier.seek(0)
            for chunk in iter(lambda: doc.fichier.read(8192), b''):
                sha256.update(chunk)
            hash_actuel = sha256.hexdigest()
            valide = hash_actuel == doc.hash_sha256
            return Response({
                'valide': valide,
                'hash_enregistre': doc.hash_sha256,
                'hash_actuel': hash_actuel,
                'message': 'Intégrité confirmée.' if valide else 'ATTENTION : le fichier a été modifié.'
            })
        except Exception as e:
            return Response({'valide': False, 'message': str(e)}, status=500)

    # ---- VERSIONING ----

    @action(detail=True, methods=['post'])
    def nouvelle_version(self, request, pk=None):
        """Téléverse une nouvelle version du document."""
        doc_original = self.get_object()
        fichier = request.FILES.get('fichier')
        commentaire = request.data.get('commentaire', '')
        if not fichier:
            return Response({'error': 'Fichier requis.'}, status=400)

        # Archive la version actuelle
        DocumentVersion.objects.get_or_create(
            document=doc_original,
            numero_version=doc_original.version,
            defaults={
                'fichier': doc_original.fichier,
                'nom_fichier_original': doc_original.nom_fichier_original,
                'hash_sha256': doc_original.hash_sha256,
                'taille_fichier': doc_original.taille_fichier,
                'auteur': doc_original.auteur,
                'commentaire': 'Version précédente archivée automatiquement',
            }
        )

        # Met à jour le document principal
        doc_original.fichier = fichier
        doc_original.hash_sha256 = ''  # sera recalculé dans save()
        doc_original.version += 1
        doc_original.save()

        # Crée l'entrée de version
        DocumentVersion.objects.create(
            document=doc_original,
            numero_version=doc_original.version,
            fichier=fichier,
            auteur=request.user,
            commentaire=commentaire,
        )

        _log(doc_original, request.user, 'nouvelle_version',
             details=f"v{doc_original.version} — {commentaire}", request=request)
        _extraire_et_sauver_texte(doc_original)
        return Response(DocumentDetailSerializer(doc_original).data)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        doc = self.get_object()
        versions = doc.historique_versions.all()
        return Response(DocumentVersionSerializer(versions, many=True).data)

    # ---- PARTAGE PUBLIC ----

    @action(detail=True, methods=['post'])
    def creer_lien_partage(self, request, pk=None):
        doc = self.get_object()
        if not _peut_acceder(request.user, doc):
            return Response({'detail': 'Accès refusé.'}, status=403)
        mot_de_passe = request.data.get('mot_de_passe', '')
        lien = DocumentShareLink.objects.create(
            document=doc,
            cree_par=request.user,
            expire_le=request.data.get('expire_le') or None,
            mot_de_passe_hash=make_password(mot_de_passe) if mot_de_passe else '',
        )
        _log(doc, request.user, 'partage_cree', request=request)
        return Response(DocumentShareLinkSerializer(lien).data, status=201)

    @action(detail=True, methods=['post'])
    def revoquer_lien_partage(self, request, pk=None):
        doc = self.get_object()
        lien_id = request.data.get('lien_id')
        lien = DocumentShareLink.objects.filter(pk=lien_id, document=doc).first()
        if not lien:
            return Response({'error': 'Lien introuvable.'}, status=404)
        lien.actif = False
        lien.save(update_fields=['actif'])
        _log(doc, request.user, 'partage_revoque', request=request)
        return Response({'detail': 'Lien révoqué.'})

    # ---- DEMANDE DE DESTRUCTION (rétention légale) ----

    @action(detail=True, methods=['post'])
    def demander_destruction(self, request, pk=None):
        doc = self.get_object()
        if doc.statut != 'archive':
            return Response({'error': "Seul un document archivé peut faire l'objet d'une demande de destruction."}, status=400)
        demande = DemandeDestruction.objects.create(
            document=doc,
            demande_par=request.user,
            motif=request.data.get('motif', ''),
        )
        _log(doc, request.user, 'destruction_demandee', details=demande.motif, request=request)
        return Response(DemandeDestructionSerializer(demande).data, status=201)

    # ---- GESTION DES ACCÈS ----

    @action(detail=True, methods=['post'])
    def accorder_acces(self, request, pk=None):
        doc = self.get_object()
        user_id = request.data.get('user_id')
        droit = request.data.get('droit', 'lecture')
        if not user_id:
            return Response({'error': 'user_id requis.'}, status=400)
        from django.contrib.auth.models import User as AuthUser
        try:
            user = AuthUser.objects.get(pk=user_id)
        except AuthUser.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)
        acces, created = DocumentAccess.objects.get_or_create(
            document=doc, user=user, droit=droit,
            defaults={'accorde_par': request.user}
        )
        return Response(DocumentAccessSerializer(acces).data, status=201 if created else 200)

    @action(detail=True, methods=['post'])
    def revoquer_acces(self, request, pk=None):
        doc = self.get_object()
        user_id = request.data.get('user_id')
        DocumentAccess.objects.filter(document=doc, user_id=user_id).delete()
        return Response({'detail': 'Accès révoqué.'})

    # ---- JOURNAL & LOGS ----

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        doc = self.get_object()
        logs = doc.logs.all()
        return Response(DocumentLogSerializer(logs, many=True).data)

    # ---- TÉLÉCHARGEMENT ----

    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        doc = self.get_object()
        if not _peut_acceder(request.user, doc):
            _log(doc, request.user, 'acces_refuse', request=request)
            return Response({'detail': 'Accès refusé.'}, status=403)
        _log(doc, request.user, 'telechargement', request=request)
        return Response({'url': request.build_absolute_uri(doc.fichier.url)})

    # ---- STATISTIQUES ----

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        stats = {
            'total_documents': qs.count(),
            'par_statut': list(qs.values('statut').annotate(count=Count('id'))),
            'par_categorie': list(
                qs.values('categorie__nom').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'par_type_fichier': list(qs.values('type_fichier').annotate(count=Count('id'))),
            'par_service': list(
                qs.values('service__nom').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'volume_total_octets': qs.aggregate(total=Sum('taille_fichier'))['total'] or 0,
            'archives': qs.filter(statut='archive').count(),
            'en_attente_validation': qs.filter(statut='en_validation').count(),
        }
        return Response(stats)

    # ---- BORDEREAU D'ARCHIVAGE ----

    @action(detail=False, methods=['get'])
    def bordereau(self, request):
        """Génère un bordereau listant les documents archivés."""
        qs = self.get_queryset().filter(statut='archive')
        if request.query_params.get('service'):
            qs = qs.filter(service_id=request.query_params['service'])
        data = {
            'date_generation': timezone.now().isoformat(),
            'genere_par': request.user.get_full_name() or request.user.username,
            'nombre_documents': qs.count(),
            'documents': DocumentListSerializer(qs, many=True).data,
        }
        return Response(data)


class DocumentLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if _is_ged_admin(self.request.user):
            return DocumentLog.objects.all()
        return DocumentLog.objects.filter(utilisateur=self.request.user)


class DemandeDestructionViewSet(viewsets.ReadOnlyModelViewSet):
    """Demandes de destruction en attente d'arbitrage — décision réservée au
    Service Information & Documentation / Direction Générale / Admin."""
    serializer_class = DemandeDestructionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DemandeDestruction.objects.select_related('document', 'demande_par', 'decide_par')
        if _is_ged_admin(self.request.user):
            return qs
        return qs.filter(demande_par=self.request.user)

    @action(detail=True, methods=['post'])
    def decider(self, request, pk=None):
        if not _is_ged_admin(request.user):
            return Response({'detail': 'Accès refusé.'}, status=403)
        demande = self.get_object()
        if demande.statut != 'EN_ATTENTE':
            return Response({'error': 'Cette demande a déjà été traitée.'}, status=400)
        decision = request.data.get('decision')
        if decision not in ('APPROUVEE', 'REJETEE'):
            return Response({'error': "decision doit être 'APPROUVEE' ou 'REJETEE'."}, status=400)

        demande.decide_par = request.user
        demande.motif_decision = request.data.get('motif_decision', '')
        demande.date_decision = timezone.now()

        if decision == 'APPROUVEE':
            demande.statut = 'EXECUTEE'
            doc = demande.document
            doc.est_supprime = True
            doc.supprime_le = timezone.now()
            doc.supprime_par = request.user
            doc.save(update_fields=['est_supprime', 'supprime_le', 'supprime_par'])
            _log(doc, request.user, 'destruction_approuvee', details=demande.motif_decision, request=request)
        else:
            demande.statut = 'REJETEE'
            _log(demande.document, request.user, 'destruction_rejetee', details=demande.motif_decision, request=request)

        demande.save(update_fields=['decide_par', 'motif_decision', 'date_decision', 'statut'])
        return Response(DemandeDestructionSerializer(demande).data)


# ── Accès public par lien de partage (sans compte) ─────────────────────────

class SharedDocumentView(APIView):
    """Consultation d'un document via lien de partage public : GET pour les
    métadonnées, POST (avec mot de passe si requis) pour le téléchargement."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _get_lien(self, token):
        lien = DocumentShareLink.objects.select_related('document').filter(token=token).first()
        if not lien or not lien.actif or lien.est_expire:
            return None
        return lien

    def get(self, request, token):
        lien = self._get_lien(token)
        if not lien:
            return Response({'detail': 'Lien invalide ou expiré.'}, status=404)
        doc = lien.document
        _log(doc, None, 'partage_consulte', details=f"via lien {token}", request=request)
        return Response({
            'titre': doc.titre,
            'reference': doc.reference,
            'type_fichier': doc.type_fichier,
            'taille_fichier': doc.taille_fichier,
            'date_document': doc.date_document,
            'protege_par_mot_de_passe': bool(lien.mot_de_passe_hash),
        })

    def post(self, request, token):
        lien = self._get_lien(token)
        if not lien:
            return Response({'detail': 'Lien invalide ou expiré.'}, status=404)
        if lien.mot_de_passe_hash and not check_password(request.data.get('mot_de_passe', ''), lien.mot_de_passe_hash):
            return Response({'detail': 'Mot de passe incorrect.'}, status=403)
        lien.nombre_acces += 1
        lien.save(update_fields=['nombre_acces'])
        doc = lien.document
        _log(doc, None, 'partage_telecharge', details=f"via lien {token}", request=request)
        return Response({'url': request.build_absolute_uri(doc.fichier.url)})


# ── Listes de liaison GED ─────────────────────────────────────────────────────
# Ces endpoints retournent toutes les entrées (sans filtrage par rôle)
# afin de permettre la création/filtrage de documents GED liés à n'importe quel objet.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ged_courriers_disponibles(request):
    from .models import Courrier
    qs = Courrier.objects.values('id', 'reference', 'objet').order_by('-created_at')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ged_diligences_disponibles(request):
    from .models import Diligence
    qs = Diligence.objects.values('id', 'reference_courrier', 'objet').order_by('-created_at')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ged_reunions_disponibles(request):
    from .models import Reunion
    qs = Reunion.objects.values('id', 'intitule').order_by('-date_debut')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ged_taches_disponibles(request):
    from .models import Tache
    qs = Tache.objects.values('id', 'titre').order_by('-createdAt')
    return Response(list(qs))
