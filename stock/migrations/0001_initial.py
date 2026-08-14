from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demandes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entrepot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('adresse', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Domaine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Emplacement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('allee', models.CharField(blank=True, max_length=50)),
                ('rayon', models.CharField(blank=True, max_length=50)),
                ('entrepot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emplacements', to='stock.entrepot')),
            ],
        ),
        migrations.CreateModel(
            name='CategorieArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('domaine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', to='stock.domaine')),
            ],
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_interne', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('unite_mesure', models.CharField(default='UNITE', max_length=50)),
                ('quantite_stock', models.FloatField(default=0)),
                ('seuil_alerte', models.FloatField(default=0)),
                ('est_critique', models.BooleanField(default=False)),
                ('categorie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articles', to='stock.categoriearticle')),
                ('emplacement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='articles', to='stock.emplacement')),
            ],
        ),
        migrations.CreateModel(
            name='Lot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_lot', models.CharField(max_length=100)),
                ('quantite_attendue', models.FloatField(default=0)),
                ('quantite_initiale', models.FloatField(default=0)),
                ('quantite_restante', models.FloatField(default=0)),
                ('unite', models.CharField(default='UNITE', max_length=50)),
                ('date_peremption', models.DateField(blank=True, null=True)),
                ('ouvert', models.BooleanField(default=False)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lots', to='stock.article')),
                ('emplacement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lots', to='stock.emplacement')),
            ],
            options={
                'unique_together': {('article', 'numero_lot')},
            },
        ),
        migrations.CreateModel(
            name='Alerte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('type_alerte', models.CharField(choices=[('STOCK_CRITIQUE', 'Stock critique'), ('RUPTURE', 'Rupture'), ('PEREMPTION', 'Péremption'), ('QUARANTAINE', 'Quarantaine')], max_length=50)),
                ('niveau_priorite', models.CharField(choices=[('CRITIQUE', 'Critique'), ('URGENT', 'Urgent'), ('AVERTISSEMENT', 'Avertissement')], max_length=20)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('traitee', models.BooleanField(default=False)),
                ('commentaire', models.TextField(blank=True)),
                ('date_traitement', models.DateTimeField(blank=True, null=True)),
                ('traite_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alertes_traitees', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Quarantaine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motif', models.TextField()),
                ('date_mise_en_quarantaine', models.DateTimeField(auto_now_add=True)),
                ('levee', models.BooleanField(default=False)),
                ('date_levee', models.DateTimeField(blank=True, null=True)),
                ('decision', models.CharField(blank=True, max_length=100)),
                ('commentaire', models.TextField(blank=True)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quarantaines', to='stock.lot')),
                ('mis_en_quarantaine_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quarantaines_creees', to=settings.AUTH_USER_MODEL)),
                ('leve_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quarantaines_levees', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Reception',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_reception', models.CharField(max_length=100, unique=True)),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_livraison_prevue', models.DateField(blank=True, null=True)),
                ('numero_commande', models.CharField(blank=True, max_length=100)),
                ('numero_bl', models.CharField(blank=True, max_length=100)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('VERIFIEE', 'Vérifiée'), ('VALIDEE', 'Validée'), ('REJETEE', 'Rejetée')], default='EN_COURS', max_length=20)),
                ('observations', models.TextField(blank=True)),
                ('date_verification', models.DateTimeField(blank=True, null=True)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('fournisseur', models.ForeignKey(blank=True, limit_choices_to={'client_profile__role': 'FOURNISSEUR'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receptions_fournisseur', to=settings.AUTH_USER_MODEL)),
                ('receptionne_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receptions_effectuees', to=settings.AUTH_USER_MODEL)),
                ('verifie_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receptions_verifiees', to=settings.AUTH_USER_MODEL)),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receptions_validees', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LigneReception',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite_attendue', models.FloatField(default=0)),
                ('quantite_recue', models.FloatField(default=0)),
                ('unite', models.CharField(blank=True, max_length=50)),
                ('numero_lot', models.CharField(blank=True, max_length=100)),
                ('date_fabrication', models.DateField(blank=True, null=True)),
                ('date_peremption', models.DateField(blank=True, null=True)),
                ('conforme', models.BooleanField(default=True)),
                ('observations', models.TextField(blank=True)),
                ('reception', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='stock.reception')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.article')),
                ('lot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.lot')),
            ],
        ),
        migrations.CreateModel(
            name='TransfertInterne',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.FloatField(default=0)),
                ('unite', models.CharField(default='UNITE', max_length=50)),
                ('motif', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('valide', models.BooleanField(default=False)),
                ('execute', models.BooleanField(default=False)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferts', to='stock.lot')),
                ('emplacement_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transferts_source', to='stock.emplacement')),
                ('emplacement_destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transferts_destination', to='stock.emplacement')),
            ],
        ),
        migrations.CreateModel(
            name='SortieStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_sortie', models.CharField(max_length=100, unique=True)),
                ('quantite', models.FloatField()),
                ('type_sortie', models.CharField(choices=[('CONSOMMATION', 'Consommation laboratoire'), ('ANALYSE', 'Utilisation pour analyse'), ('PERTE', 'Perte/Casse'), ('PEREMPTION', 'Péremption'), ('RETOUR_FOURNISSEUR', 'Retour fournisseur'), ('DESTRUCTION', 'Destruction'), ('AUTRE', 'Autre')], max_length=50)),
                ('motif', models.TextField(blank=True)),
                ('date_sortie', models.DateTimeField(auto_now_add=True)),
                ('valide', models.BooleanField(default=False)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sorties', to='stock.lot')),
                ('demande_devis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sorties_stock', to='demandes.demandedevis')),
                ('utilisateur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sorties_stock', to=settings.AUTH_USER_MODEL)),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sorties_validees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_sortie'],
            },
        ),
        migrations.CreateModel(
            name='MouvementStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie'), ('TRANSFERT', 'Transfert'), ('AJUSTEMENT', 'Ajustement inventaire'), ('QUARANTAINE_ENTREE', 'Mise en quarantaine'), ('QUARANTAINE_SORTIE', 'Sortie de quarantaine')], max_length=50)),
                ('quantite', models.FloatField()),
                ('quantite_avant', models.FloatField(default=0)),
                ('quantite_apres', models.FloatField(default=0)),
                ('reference_document', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('date_mouvement', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='stock.article')),
                ('lot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='stock.lot')),
                ('reception', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mouvements', to='stock.reception')),
                ('sortie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mouvements', to='stock.sortiestock')),
                ('transfert', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mouvements', to='stock.transfertinterne')),
                ('utilisateur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mouvements_stock', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_mouvement'],
            },
        ),
        migrations.CreateModel(
            name='Inventaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_inventaire', models.CharField(max_length=100, unique=True)),
                ('type_inventaire', models.CharField(choices=[('COMPLET', 'Inventaire complet'), ('PARTIEL', 'Inventaire partiel'), ('TOURNANT', 'Inventaire tournant'), ('ANNUEL', 'Inventaire annuel')], default='COMPLET', max_length=50)),
                ('statut', models.CharField(choices=[('PLANIFIE', 'Planifié'), ('EN_COURS', 'En cours'), ('TERMINE', 'Terminé'), ('VALIDE', 'Validé'), ('ANNULE', 'Annulé')], default='PLANIFIE', max_length=20)),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('observations', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('entrepot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventaires', to='stock.entrepot')),
                ('responsable', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventaires_responsable', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_debut'],
            },
        ),
        migrations.CreateModel(
            name='LigneInventaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite_theorique', models.FloatField(default=0)),
                ('quantite_comptee', models.FloatField(blank=True, null=True)),
                ('ecart', models.FloatField(default=0)),
                ('commentaire', models.TextField(blank=True)),
                ('date_comptage', models.DateTimeField(blank=True, null=True)),
                ('inventaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='stock.inventaire')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes_inventaire', to='stock.article')),
                ('lot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lignes_inventaire', to='stock.lot')),
                ('emplacement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock.emplacement')),
                ('compte_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lignes_inventaire_comptees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['article__designation'],
            },
        ),
    ]
