from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionCommunication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('CAMPAGNE', 'Campagne de communication'), ('COMMUNIQUE', 'Communiqué de presse'), ('EVENEMENT', 'Événement'), ('SALON', 'Salon / foire'), ('SUPPORT', 'Support de communication')], max_length=20)),
                ('titre', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('EN_COURS', 'En cours'), ('REALISEE', 'Réalisée'), ('ANNULEE', 'Annulée')], default='PLANIFIEE', max_length=20)),
                ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('chiffre_affaires_genere', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_communication', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Partenariat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_partenaire', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('date_signature', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_NEGOCIATION', 'En négociation'), ('ACTIF', 'Actif'), ('TERMINE', 'Terminé')], default='EN_NEGOCIATION', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partenariats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SatisfactionClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_nom', models.CharField(max_length=255)),
                ('note', models.PositiveSmallIntegerField(help_text='Note sur 5')),
                ('fidele', models.BooleanField(default=False, help_text='Client fidélisé (renouvellement)')),
                ('commentaire', models.TextField(blank=True)),
                ('date_enquete', models.DateField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date_enquete'],
            },
        ),
        migrations.CreateModel(
            name='Prospect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('organisation', models.CharField(blank=True, max_length=255)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('contact_telephone', models.CharField(blank=True, max_length=50)),
                ('source', models.CharField(blank=True, max_length=100)),
                ('statut', models.CharField(choices=[('NOUVEAU', 'Nouveau'), ('QUALIFIE', 'Qualifié'), ('DEVIS_ENVOYE', 'Devis envoyé'), ('CONVERTI', 'Converti en client'), ('PERDU', 'Perdu')], default='NOUVEAU', max_length=20)),
                ('montant_devis', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_conversion', models.DateTimeField(blank=True, null=True)),
                ('action_origine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prospects', to='dg_communication.actioncommunication')),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
