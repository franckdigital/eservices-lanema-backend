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
            name='PieceComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('type_piece', models.CharField(choices=[('FACTURE_CLIENT', 'Facture client'), ('FACTURE_FOURNISSEUR', 'Facture fournisseur'), ('RECU', 'Reçu'), ('BON_COMMANDE', 'Bon de commande'), ('AUTRE', 'Autre')], default='AUTRE', max_length=25)),
                ('source_reference', models.CharField(blank=True, help_text="Numero du document d'origine (ex: numero de facture)", max_length=100)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date_piece', models.DateField(auto_now_add=True)),
                ('fichier', models.FileField(blank=True, null=True, upload_to='comptabilite/pieces/')),
                ('statut', models.CharField(choices=[('ENREGISTREE', 'Enregistrée'), ('VALIDEE', 'Validée'), ('REJETEE', 'Rejetée')], default='ENREGISTREE', max_length=15)),
                ('date_validation', models.DateField(blank=True, null=True)),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pieces_validees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_piece'],
            },
        ),
    ]
