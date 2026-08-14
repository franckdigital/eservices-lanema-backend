from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fournisseur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('contact', models.CharField(blank=True, max_length=255)),
                ('actif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Marche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('objet', models.CharField(max_length=255)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('date_attribution', models.DateField(blank=True, null=True)),
                ('respect_plan', models.BooleanField(default=True, help_text='Conforme au plan de passation des marchés')),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('ATTRIBUE', 'Attribué'), ('EXECUTE', 'Exécuté'), ('ANNULE', 'Annulé')], default='EN_COURS', max_length=20)),
            ],
            options={
                'ordering': ['-date_attribution'],
            },
        ),
        migrations.CreateModel(
            name='DemandeAchat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('objet', models.CharField(max_length=255)),
                ('date_demande', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('TRAITEE', 'Traitée'), ('REJETEE', 'Rejetée')], default='EN_ATTENTE', max_length=20)),
                ('demandeur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandes_achat', to=settings.AUTH_USER_MODEL)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandes_achat', to='core.direction')),
            ],
            options={
                'ordering': ['-date_demande'],
            },
        ),
        migrations.CreateModel(
            name='BonCommande',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('fournisseur_nom', models.CharField(blank=True, max_length=255)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date_commande', models.DateField(auto_now_add=True)),
                ('date_livraison_prevue', models.DateField(blank=True, null=True)),
                ('date_livraison_reelle', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('LIVRE', 'Livré'), ('EN_RETARD', 'En retard'), ('ANNULE', 'Annulé')], default='EN_COURS', max_length=20)),
                ('conforme', models.BooleanField(blank=True, null=True)),
                ('note_satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5', null=True)),
                ('demande', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bons_commande', to='daaf_achats.demandeachat')),
            ],
            options={
                'ordering': ['-date_commande'],
            },
        ),
    ]
