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
            name='Rapport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_rapport', models.CharField(choices=[('SYNTHSE_DEMANDES', 'Synthèse demandes'), ('SYNTHSE_FACTURATION', 'Synthèse facturation'), ('PERSONNALISE', 'Personnalisé')], default='PERSONNALISE', max_length=50)),
                ('titre', models.CharField(max_length=255)),
                ('parametres', models.JSONField(blank=True, default=dict)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rapports', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
