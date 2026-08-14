from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qualite', '0002_dea_kpis'),
        ('facturation', '0003_boncommande_signatures'),
    ]

    operations = [
        # Repointage du FK vers facturation.DemandeAnalyse (au lieu de
        # demandes.DemandeDevis) : les echantillons ne sont receptionnes
        # qu'une fois le paiement valide et la demande d'analyse creee. On
        # supprime puis recree le champ plutot que de retargeter en place,
        # pour eviter que d'anciennes valeurs ne pointent silencieusement
        # vers un mauvais enregistrement.
        migrations.RemoveField(
            model_name='echantillon',
            name='demande',
        ),
        migrations.AddField(
            model_name='echantillon',
            name='demande',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text="Demande d'analyse (le paiement doit etre valide avant reception des echantillons)",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='echantillons',
                to='facturation.demandeanalyse',
            ),
        ),
    ]
