from rest_framework import serializers

from .models import (
    Entrepot,
    Emplacement,
    Domaine,
    CategorieArticle,
    Article,
    Lot,
    Alerte,
    Quarantaine,
    Reception,
    LigneReception,
    TransfertInterne,
    SortieStock,
    MouvementStock,
    Inventaire,
    LigneInventaire,
)


class EntrepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrepot
        fields = ["id", "nom", "code", "adresse"]


class EmplacementSerializer(serializers.ModelSerializer):
    entrepot_details = serializers.SerializerMethodField()
    capacite_utilisee = serializers.SerializerMethodField()

    class Meta:
        model = Emplacement
        fields = ["id", "code", "entrepot", "entrepot_details", "allee", "rayon", "capacite_utilisee"]
    
    def get_entrepot_details(self, obj):
        if obj.entrepot:
            return {
                "id": obj.entrepot.id,
                "nom": obj.entrepot.nom,
                "code": obj.entrepot.code
            }
        return None
    
    def get_capacite_utilisee(self, obj):
        # Calculer la capacité utilisée basée sur les lots dans cet emplacement
        total_lots = obj.lots.count() if hasattr(obj, 'lots') else 0
        total_quantite = sum(lot.quantite_restante for lot in obj.lots.all()) if hasattr(obj, 'lots') else 0
        # Retourner le nombre de lots ou un pourcentage basé sur une capacité estimée
        if total_lots > 0:
            # Estimation: 100 unités = 100% pour un emplacement
            return min(int((total_quantite / 100) * 100), 100)
        return 0


class DomaineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domaine
        fields = ["id", "nom", "code", "description"]


class CategorieArticleSerializer(serializers.ModelSerializer):
    domaine_details = serializers.SerializerMethodField()
    domaine = serializers.PrimaryKeyRelatedField(
        queryset=Domaine.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = CategorieArticle
        fields = ["id", "nom", "code", "domaine", "domaine_details"]
    
    def get_domaine_details(self, obj):
        if obj.domaine:
            return {"id": obj.domaine.id, "nom": obj.domaine.nom, "code": obj.domaine.code}
        return None
    
    def to_internal_value(self, data):
        # Si domaine est une string vide, le convertir en None
        if 'domaine' in data and data['domaine'] == '':
            data = data.copy()
            data['domaine'] = None
        return super().to_internal_value(data)


class ArticleSerializer(serializers.ModelSerializer):
    categorie = CategorieArticleSerializer(read_only=True)
    categorie_id = serializers.PrimaryKeyRelatedField(
        source="categorie", queryset=CategorieArticle.objects.all(), write_only=True, required=False, allow_null=True
    )
    emplacement_code = serializers.CharField(source="emplacement.code", read_only=True, allow_null=True)
    emplacement_id = serializers.PrimaryKeyRelatedField(
        source="emplacement", queryset=Emplacement.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Article
        fields = [
            "id",
            "reference_interne",
            "designation",
            "unite_mesure",
            "quantite_stock",
            "seuil_alerte",
            "est_critique",
            "prix_unitaire",
            "categorie",
            "categorie_id",
            "emplacement",
            "emplacement_id",
            "emplacement_code",
        ]


class LotSerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)
    article_id = serializers.PrimaryKeyRelatedField(
        source="article", queryset=Article.objects.all(), write_only=True
    )
    emplacement_code = serializers.CharField(source="emplacement.code", read_only=True, allow_null=True)
    emplacement_id = serializers.PrimaryKeyRelatedField(
        source="emplacement", queryset=Emplacement.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Lot
        fields = [
            "id",
            "article",
            "article_id",
            "numero_lot",
            "quantite_attendue",
            "quantite_initiale",
            "quantite_restante",
            "unite",
            "date_peremption",
            "ouvert",
            "emplacement",
            "emplacement_id",
            "emplacement_code",
        ]


class AlerteSerializer(serializers.ModelSerializer):
    traite_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Alerte
        fields = [
            "id",
            "titre",
            "message",
            "type_alerte",
            "niveau_priorite",
            "date_creation",
            "traitee",
            "commentaire",
            "date_traitement",
            "traite_par",
            "traite_par_nom",
        ]

    def get_traite_par_nom(self, obj):
        if not obj.traite_par:
            return None
        return obj.traite_par.get_full_name() or obj.traite_par.username


class QuarantaineSerializer(serializers.ModelSerializer):
    lot = LotSerializer(read_only=True)
    lot_id = serializers.PrimaryKeyRelatedField(
        source="lot", queryset=Lot.objects.all(), write_only=True
    )
    lot_numero = serializers.CharField(source="lot.numero_lot", read_only=True)
    article_nom = serializers.CharField(source="lot.article.designation", read_only=True)
    statut = serializers.SerializerMethodField()
    mis_en_quarantaine_par_nom = serializers.SerializerMethodField()
    leve_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Quarantaine
        fields = [
            "id",
            "lot",
            "lot_id",
            "lot_numero",
            "article_nom",
            "motif",
            "date_mise_en_quarantaine",
            "mis_en_quarantaine_par",
            "mis_en_quarantaine_par_nom",
            "levee",
            "date_levee",
            "leve_par",
            "leve_par_nom",
            "decision",
            "commentaire",
            "statut",
        ]
        read_only_fields = ["date_mise_en_quarantaine", "date_levee"]

    def get_statut(self, obj):
        return "LEVEE" if obj.levee else "EN_COURS"

    def get_mis_en_quarantaine_par_nom(self, obj):
        if obj.mis_en_quarantaine_par:
            return f"{obj.mis_en_quarantaine_par.first_name} {obj.mis_en_quarantaine_par.last_name}".strip() or obj.mis_en_quarantaine_par.email
        return "Système"

    def get_leve_par_nom(self, obj):
        if obj.leve_par:
            return f"{obj.leve_par.first_name} {obj.leve_par.last_name}".strip() or obj.leve_par.email
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['mis_en_quarantaine_par'] = request.user
        return super().create(validated_data)


class LigneReceptionCreateSerializer(serializers.Serializer):
    """Serializer pour la création de lignes de réception (nested)"""
    article = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all())
    quantite_attendue = serializers.FloatField(default=0)
    quantite_recue = serializers.FloatField(default=0)
    unite = serializers.CharField(max_length=50, required=False, allow_blank=True)
    numero_lot = serializers.CharField(max_length=100, required=False, allow_blank=True)
    date_fabrication = serializers.DateField(required=False, allow_null=True)
    date_peremption = serializers.DateField(required=False, allow_null=True)
    conforme = serializers.BooleanField(default=True)
    observations = serializers.CharField(required=False, allow_blank=True)


class LigneReceptionSerializer(serializers.ModelSerializer):
    article_nom = serializers.CharField(source="article.designation", read_only=True)
    article_reference = serializers.CharField(source="article.reference_interne", read_only=True)
    lot_cree = serializers.SerializerMethodField()

    class Meta:
        model = LigneReception
        fields = [
            "id", "reception", "article", "article_nom", "article_reference", 
            "lot", "lot_cree", "quantite_attendue", "quantite_recue", "unite",
            "numero_lot", "date_fabrication", "date_peremption", "conforme", "observations"
        ]
        read_only_fields = ["id", "reception", "lot", "lot_cree"]
    
    def get_lot_cree(self, obj):
        if obj.lot:
            return {
                "id": obj.lot.id,
                "numero_lot": obj.lot.numero_lot,
                "statut": "ACTIF" if obj.lot.quantite_restante > 0 else "EPUISE"
            }
        return None


class ReceptionSerializer(serializers.ModelSerializer):
    lignes = LigneReceptionCreateSerializer(many=True, required=False, write_only=True)
    lignes_detail = LigneReceptionSerializer(source='lignes', many=True, read_only=True)
    fournisseur_nom = serializers.SerializerMethodField()
    nombre_lignes = serializers.SerializerMethodField()
    receptionne_par_nom = serializers.SerializerMethodField()
    verifie_par_nom = serializers.SerializerMethodField()
    valide_par_nom = serializers.SerializerMethodField()
    conforme = serializers.SerializerMethodField()

    class Meta:
        model = Reception
        fields = [
            "id", "numero_reception", "fournisseur", "fournisseur_nom",
            "date_reception", "date_livraison_prevue", "numero_commande", "numero_bl",
            "statut", "observations", "lignes", "lignes_detail", "nombre_lignes", "conforme",
            "receptionne_par", "receptionne_par_nom",
            "verifie_par", "verifie_par_nom", "date_verification",
            "valide_par", "valide_par_nom", "date_validation"
        ]
        read_only_fields = ["id", "numero_reception", "date_reception"]
    
    def get_fournisseur_nom(self, obj):
        if obj.fournisseur:
            profile = getattr(obj.fournisseur, "client_profile", None)
            return getattr(profile, "raison_sociale", "") or obj.fournisseur.email
        return None
    
    def get_conforme(self, obj):
        return obj.conforme
    
    def get_nombre_lignes(self, obj):
        return obj.lignes.count()
    
    def get_receptionne_par_nom(self, obj):
        if obj.receptionne_par:
            return f"{obj.receptionne_par.first_name} {obj.receptionne_par.last_name}".strip() or obj.receptionne_par.email
        return "Système"
    
    def get_verifie_par_nom(self, obj):
        if obj.verifie_par:
            return f"{obj.verifie_par.first_name} {obj.verifie_par.last_name}".strip() or obj.verifie_par.email
        return None
    
    def get_valide_par_nom(self, obj):
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}".strip() or obj.valide_par.email
        return None
    
    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        user = self.context.get('request').user if self.context.get('request') else None
        
        # Créer la réception
        reception = Reception.objects.create(
            receptionne_par=user,
            **validated_data
        )
        
        # Créer les lignes de réception et les lots associés
        for ligne_data in lignes_data:
            article = ligne_data.get('article')
            quantite_attendue = ligne_data.get('quantite_attendue', 0)
            quantite_recue = ligne_data.get('quantite_recue', 0)
            numero_lot = ligne_data.get('numero_lot', '')
            date_fabrication = ligne_data.get('date_fabrication')
            date_peremption = ligne_data.get('date_peremption')
            unite = ligne_data.get('unite') or (article.unite_mesure if article else 'UNITE')
            conforme = ligne_data.get('conforme', True)
            observations = ligne_data.get('observations', '')
            
            # Créer le lot si quantité reçue > 0
            lot = None
            if quantite_recue > 0 and article:
                # Récupérer l'emplacement de l'article s'il existe
                emplacement = getattr(article, 'emplacement', None)
                
                lot = Lot.objects.create(
                    article=article,
                    numero_lot=numero_lot or f"LOT-{reception.numero_reception}-{article.id}",
                    quantite_attendue=quantite_attendue or quantite_recue,
                    quantite_initiale=quantite_recue,
                    quantite_restante=quantite_recue,
                    unite=unite,
                    date_peremption=date_peremption,
                    ouvert=False,
                    emplacement=emplacement,
                )
                # Mettre à jour le stock de l'article
                article.quantite_stock = (article.quantite_stock or 0) + quantite_recue
                article.save(update_fields=['quantite_stock'])
            
            LigneReception.objects.create(
                reception=reception,
                article=article,
                lot=lot,
                quantite_attendue=quantite_attendue,
                quantite_recue=quantite_recue,
                unite=unite,
                numero_lot=numero_lot,
                date_fabrication=date_fabrication,
                date_peremption=date_peremption,
                conforme=conforme,
                observations=observations,
            )
        
        return reception


class TransfertInterneSerializer(serializers.ModelSerializer):
    lot_details = LotSerializer(source="lot", read_only=True)
    lot_numero = serializers.CharField(source="lot.numero_lot", read_only=True)
    article_nom = serializers.CharField(source="lot.article.designation", read_only=True)
    emplacement_source_details = EmplacementSerializer(source="emplacement_source", read_only=True)
    emplacement_source_code = serializers.SerializerMethodField()
    emplacement_destination_details = EmplacementSerializer(source="emplacement_destination", read_only=True)
    emplacement_destination_code = serializers.CharField(source="emplacement_destination.code", read_only=True)
    statut = serializers.SerializerMethodField()
    numero_transfert = serializers.SerializerMethodField()
    date_demande = serializers.DateTimeField(source="date_creation", read_only=True)

    quantite_transferee = serializers.FloatField(source='quantite', read_only=True)
    
    class Meta:
        model = TransfertInterne
        fields = [
            "id",
            "numero_transfert",
            "lot",
            "lot_details",
            "lot_numero",
            "article_nom",
            "emplacement_source",
            "emplacement_source_details",
            "emplacement_source_code",
            "emplacement_destination",
            "emplacement_destination_details",
            "emplacement_destination_code",
            "quantite",
            "quantite_transferee",
            "unite",
            "motif",
            "date_creation",
            "date_demande",
            "valide",
            "execute",
            "statut",
        ]
    
    def get_emplacement_source_code(self, obj):
        if obj.emplacement_source:
            return obj.emplacement_source.code
        return "Placement initial"
    
    def get_statut(self, obj):
        if obj.execute:
            return "EXECUTE"
        elif obj.valide:
            return "VALIDE"
        else:
            return "EN_ATTENTE"
    
    def get_numero_transfert(self, obj):
        return f"TRF-{obj.id:05d}"
    
    def create(self, validated_data):
        # Créer le transfert
        transfert = super().create(validated_data)
        
        lot = transfert.lot
        quantite_transferee = transfert.quantite or 0
        
        # Si c'est un placement initial (pas d'emplacement source), on définit l'emplacement du lot
        if not transfert.emplacement_source:
            lot.emplacement = transfert.emplacement_destination
            lot.save(update_fields=['emplacement'])
        else:
            # Sinon c'est un vrai transfert: diminuer la quantité restante du lot source
            if quantite_transferee > 0:
                lot.quantite_restante = max(0, (lot.quantite_restante or 0) - quantite_transferee)
                lot.save(update_fields=['quantite_restante'])
                
                # Mettre à jour le stock de l'article
                article = lot.article
                if article:
                    article.quantite_stock = max(0, (article.quantite_stock or 0) - quantite_transferee)
                    article.save(update_fields=['quantite_stock'])
        
        # Marquer le transfert comme exécuté
        transfert.execute = True
        transfert.save(update_fields=['execute'])
        
        return transfert


class SortieStockSerializer(serializers.ModelSerializer):
    lot_details = LotSerializer(source="lot", read_only=True)
    lot_numero = serializers.CharField(source="lot.numero_lot", read_only=True)
    article_nom = serializers.CharField(source="lot.article.designation", read_only=True)
    article_reference = serializers.CharField(source="lot.article.reference_interne", read_only=True)
    unite = serializers.CharField(source="lot.unite", read_only=True)
    utilisateur_nom = serializers.SerializerMethodField()
    valide_par_nom = serializers.SerializerMethodField()
    type_sortie_display = serializers.CharField(source="get_type_sortie_display", read_only=True)

    class Meta:
        model = SortieStock
        fields = [
            "id",
            "numero_sortie",
            "lot",
            "lot_details",
            "lot_numero",
            "article_nom",
            "article_reference",
            "quantite",
            "unite",
            "type_sortie",
            "type_sortie_display",
            "motif",
            "demande_devis",
            "utilisateur",
            "utilisateur_nom",
            "date_sortie",
            "valide",
            "valide_par",
            "valide_par_nom",
            "date_validation",
        ]
        read_only_fields = ["numero_sortie", "date_sortie", "date_validation"]
    
    def get_utilisateur_nom(self, obj):
        if obj.utilisateur:
            return f"{obj.utilisateur.first_name} {obj.utilisateur.last_name}".strip() or obj.utilisateur.email
        return None
    
    def get_valide_par_nom(self, obj):
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}".strip() or obj.valide_par.email
        return None


class SortieStockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SortieStock
        fields = ["lot", "quantite", "type_sortie", "motif", "demande_devis"]
    
    def validate(self, data):
        lot = data.get("lot")
        quantite = data.get("quantite")
        
        if quantite <= 0:
            raise serializers.ValidationError({"quantite": "La quantité doit être positive."})
        
        if lot and quantite > lot.quantite_restante:
            raise serializers.ValidationError({
                "quantite": f"Quantité insuffisante dans le lot. Disponible: {lot.quantite_restante} {lot.unite}"
            })
        
        return data


class MouvementStockSerializer(serializers.ModelSerializer):
    article_details = ArticleSerializer(source="article", read_only=True)
    lot_numero = serializers.CharField(source="lot.numero_lot", read_only=True, allow_null=True)
    utilisateur_nom = serializers.SerializerMethodField()
    type_mouvement_display = serializers.CharField(source="get_type_mouvement_display", read_only=True)
    
    class Meta:
        model = MouvementStock
        fields = [
            "id",
            "article",
            "article_details",
            "lot",
            "lot_numero",
            "type_mouvement",
            "type_mouvement_display",
            "quantite",
            "quantite_avant",
            "quantite_apres",
            "reference_document",
            "description",
            "reception",
            "sortie",
            "transfert",
            "utilisateur",
            "utilisateur_nom",
            "date_mouvement",
        ]
    
    def get_utilisateur_nom(self, obj):
        if obj.utilisateur:
            return f"{obj.utilisateur.first_name} {obj.utilisateur.last_name}".strip() or obj.utilisateur.email
        return "Système"


class LigneInventaireSerializer(serializers.ModelSerializer):
    article_nom = serializers.CharField(source="article.designation", read_only=True)
    article_reference = serializers.CharField(source="article.reference_interne", read_only=True)
    lot_numero = serializers.CharField(source="lot.numero_lot", read_only=True, allow_null=True)
    emplacement_code = serializers.CharField(source="emplacement.code", read_only=True, allow_null=True)
    compte_par_nom = serializers.SerializerMethodField()
    unite = serializers.CharField(source="article.unite_mesure", read_only=True)
    
    class Meta:
        model = LigneInventaire
        fields = [
            "id",
            "inventaire",
            "article",
            "article_nom",
            "article_reference",
            "lot",
            "lot_numero",
            "emplacement",
            "emplacement_code",
            "quantite_theorique",
            "quantite_comptee",
            "ecart",
            "unite",
            "commentaire",
            "compte_par",
            "compte_par_nom",
            "date_comptage",
        ]
    
    def get_compte_par_nom(self, obj):
        if obj.compte_par:
            return f"{obj.compte_par.first_name} {obj.compte_par.last_name}".strip() or obj.compte_par.email
        return None


class InventaireSerializer(serializers.ModelSerializer):
    lignes = LigneInventaireSerializer(many=True, read_only=True)
    entrepot_nom = serializers.CharField(source="entrepot.nom", read_only=True, allow_null=True)
    responsable_nom = serializers.SerializerMethodField()
    type_inventaire_display = serializers.CharField(source="get_type_inventaire_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    nb_lignes = serializers.SerializerMethodField()
    nb_lignes_comptees = serializers.SerializerMethodField()
    total_ecarts = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventaire
        fields = [
            "id",
            "numero_inventaire",
            "type_inventaire",
            "type_inventaire_display",
            "statut",
            "statut_display",
            "entrepot",
            "entrepot_nom",
            "date_debut",
            "date_fin",
            "responsable",
            "responsable_nom",
            "observations",
            "created_at",
            "lignes",
            "nb_lignes",
            "nb_lignes_comptees",
            "total_ecarts",
        ]
        read_only_fields = ["numero_inventaire", "created_at"]
    
    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.first_name} {obj.responsable.last_name}".strip() or obj.responsable.email
        return None
    
    def get_nb_lignes(self, obj):
        return obj.lignes.count()
    
    def get_nb_lignes_comptees(self, obj):
        return obj.lignes.filter(quantite_comptee__isnull=False).count()
    
    def get_total_ecarts(self, obj):
        from django.db.models import Sum
        result = obj.lignes.filter(quantite_comptee__isnull=False).aggregate(total=Sum("ecart"))
        return result["total"] or 0


class InventaireCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventaire
        fields = ["type_inventaire", "entrepot", "date_debut", "observations"]
