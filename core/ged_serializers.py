from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    CategorieDocument, Document, DocumentVersion,
    DocumentAccess, DocumentLog, CertificatArchivage,
    DocumentShareLink, DemandeDestruction,
)


class CategorieDocumentSerializer(serializers.ModelSerializer):
    sous_categories = serializers.SerializerMethodField()
    nombre_documents = serializers.SerializerMethodField()

    def get_sous_categories(self, obj):
        return CategorieDocumentSerializer(obj.sous_categories.all(), many=True).data

    def get_nombre_documents(self, obj):
        return obj.documents.count()

    class Meta:
        model = CategorieDocument
        fields = [
            'id', 'nom', 'description', 'icone', 'parent',
            'duree_conservation_ans', 'sous_categories',
            'nombre_documents', 'created_at',
        ]


class DocumentVersionSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(source='auteur.get_full_name', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'numero_version', 'fichier', 'nom_fichier_original',
            'hash_sha256', 'taille_fichier', 'auteur', 'auteur_nom',
            'commentaire', 'created_at',
        ]
        read_only_fields = ['hash_sha256', 'taille_fichier', 'nom_fichier_original']


class DocumentAccessSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = DocumentAccess
        fields = ['id', 'document', 'user', 'user_nom', 'user_email', 'droit', 'accorde_par', 'created_at']
        read_only_fields = ['accorde_par']


class DocumentLogSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    action_label = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = DocumentLog
        fields = ['id', 'action', 'action_label', 'utilisateur', 'utilisateur_nom', 'details', 'adresse_ip', 'created_at']


class CertificatArchivageSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(source='auteur.get_full_name', read_only=True)

    class Meta:
        model = CertificatArchivage
        fields = ['id', 'numero_certificat', 'hash_sha256', 'horodatage', 'auteur', 'auteur_nom', 'valide', 'metadata']


class DocumentShareLinkSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    est_expire = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocumentShareLink
        fields = [
            'id', 'document', 'token', 'cree_par', 'cree_par_nom', 'expire_le',
            'nombre_acces', 'actif', 'est_expire', 'created_at',
        ]
        read_only_fields = ['token', 'cree_par', 'nombre_acces', 'created_at']


class DemandeDestructionSerializer(serializers.ModelSerializer):
    demande_par_nom = serializers.CharField(source='demande_par.get_full_name', read_only=True)
    decide_par_nom = serializers.CharField(source='decide_par.get_full_name', read_only=True)
    document_reference = serializers.CharField(source='document.reference', read_only=True)
    document_titre = serializers.CharField(source='document.titre', read_only=True)

    class Meta:
        model = DemandeDestruction
        fields = [
            'id', 'document', 'document_reference', 'document_titre',
            'demande_par', 'demande_par_nom', 'motif', 'statut',
            'decide_par', 'decide_par_nom', 'motif_decision',
            'date_demande', 'date_decision',
        ]
        read_only_fields = ['demande_par', 'statut', 'decide_par', 'motif_decision', 'date_demande', 'date_decision']


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes."""
    auteur_nom = serializers.CharField(source='auteur.get_full_name', read_only=True)
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    service_nom = serializers.CharField(source='service.nom', read_only=True)
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    confidentialite_label = serializers.CharField(source='get_confidentialite_display', read_only=True)
    taille_lisible = serializers.SerializerMethodField()
    source_module = serializers.SerializerMethodField()

    def get_taille_lisible(self, obj):
        taille = obj.taille_fichier
        if taille < 1024:
            return f"{taille} o"
        elif taille < 1024 ** 2:
            return f"{taille / 1024:.1f} Ko"
        else:
            return f"{taille / 1024 ** 2:.1f} Mo"

    def get_source_module(self, obj):
        if obj.content_type_id:
            return obj.content_type.model
        if obj.courrier_id:
            return 'courrier'
        if obj.diligence_id:
            return 'diligence'
        if obj.reunion_id:
            return 'reunion'
        if obj.tache_id:
            return 'tache'
        return None

    class Meta:
        model = Document
        fields = [
            'id', 'reference', 'titre', 'categorie', 'categorie_nom',
            'type_fichier', 'taille_fichier', 'taille_lisible',
            'statut', 'statut_label', 'confidentialite', 'confidentialite_label',
            'auteur', 'auteur_nom', 'service', 'service_nom',
            'date_document', 'version', 'est_version_courante',
            'est_supprime', 'source_module',
            'created_at', 'updated_at',
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail d'un document."""
    auteur_nom = serializers.CharField(source='auteur.get_full_name', read_only=True)
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    service_nom = serializers.CharField(source='service.nom', read_only=True)
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    confidentialite_label = serializers.CharField(source='get_confidentialite_display', read_only=True)
    historique_versions = DocumentVersionSerializer(many=True, read_only=True)
    acces = DocumentAccessSerializer(many=True, read_only=True)
    certificat = CertificatArchivageSerializer(read_only=True, source='certificat_archivage')
    logs_recents = serializers.SerializerMethodField()
    taille_lisible = serializers.SerializerMethodField()
    liens_partage = DocumentShareLinkSerializer(many=True, read_only=True)
    demandes_destruction = DemandeDestructionSerializer(many=True, read_only=True)
    source_module = serializers.SerializerMethodField()

    def get_logs_recents(self, obj):
        return DocumentLogSerializer(obj.logs.all()[:10], many=True).data

    def get_source_module(self, obj):
        if obj.content_type_id:
            return obj.content_type.model
        return None

    def get_taille_lisible(self, obj):
        taille = obj.taille_fichier
        if taille < 1024:
            return f"{taille} o"
        elif taille < 1024 ** 2:
            return f"{taille / 1024:.1f} Ko"
        else:
            return f"{taille / 1024 ** 2:.1f} Mo"

    class Meta:
        model = Document
        fields = [
            'id', 'reference', 'titre', 'description', 'categorie', 'categorie_nom',
            'fichier', 'type_fichier', 'taille_fichier', 'taille_lisible', 'nom_fichier_original',
            'statut', 'statut_label', 'confidentialite', 'confidentialite_label',
            'mots_cles', 'contenu_ocr',
            'auteur', 'auteur_nom', 'service', 'service_nom',
            'date_document', 'date_expiration',
            'version', 'est_version_courante', 'document_original',
            'courrier', 'diligence', 'reunion', 'tache',
            'content_type', 'object_id', 'source_module',
            'est_supprime', 'supprime_le', 'supprime_par',
            'archive_le', 'archive_par', 'duree_conservation_ans', 'date_destruction_prevue',
            'hash_sha256',
            'historique_versions', 'acces', 'certificat', 'logs_recents',
            'liens_partage', 'demandes_destruction',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'reference', 'hash_sha256', 'taille_fichier', 'nom_fichier_original',
            'est_supprime', 'supprime_le', 'supprime_par',
        ]
