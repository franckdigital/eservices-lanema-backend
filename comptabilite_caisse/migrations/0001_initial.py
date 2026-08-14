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
            name='Caisse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('solde_initial', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('actif', models.BooleanField(default=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='caisses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='MouvementCaisse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie')], max_length=10)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date_mouvement', models.DateTimeField(auto_now_add=True)),
                ('motif', models.CharField(blank=True, max_length=255)),
                ('justificatif', models.FileField(blank=True, null=True, upload_to='comptabilite/caisse/')),
                ('caisse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='comptabilite_caisse.caisse')),
            ],
            options={
                'ordering': ['-date_mouvement'],
            },
        ),
    ]
