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
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('ECHANTILLON', 'Échantillon'), ('DEMANDE', 'Demande de devis'), ('FACTURE', 'Facture'), ('RECEPTION', 'Réception'), ('SORTIE', 'Sortie de stock'), ('CLIENT', 'Client'), ('ANALYSE', 'Analyse'), ('RAPPORT', 'Rapport')], max_length=50)),
                ('titre', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('utilisateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_activity',
                'verbose_name': 'Activité',
                'verbose_name_plural': 'Activités',
                'ordering': ['-created_at'],
            },
        ),
    ]
