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
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('message', models.TextField(blank=True)),
                ('type_notification', models.CharField(choices=[('INFO', 'Information'), ('ALERTE', 'Alerte'), ('STOCK', 'Stock'), ('DEMANDE', 'Demande'), ('QUALITE', 'Qualité'), ('FACTURATION', 'Facturation'), ('METROLOGIE', 'Métrologie'), ('ECHANTILLON', 'Échantillon'), ('ESSAI', 'Essai')], default='INFO', max_length=20)),
                ('priorite', models.CharField(choices=[('BASSE', 'Basse'), ('NORMALE', 'Normale'), ('HAUTE', 'Haute'), ('URGENTE', 'Urgente')], default='NORMALE', max_length=20)),
                ('lu', models.BooleanField(default=False)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('lien', models.CharField(blank=True, help_text='Lien vers la ressource concernée', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labo_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
