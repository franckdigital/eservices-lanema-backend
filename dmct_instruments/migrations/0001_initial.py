from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dmct_clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstrumentMesure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('type_instrument', models.CharField(blank=True, max_length=255)),
                ('statut', models.CharField(choices=[('EN_SERVICE', 'En service'), ('IMMOBILISE', 'Immobilisé')], default='EN_SERVICE', max_length=20)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instruments', to='dmct_clients.clientdmct')),
            ],
            options={
                'ordering': ['designation'],
            },
        ),
        migrations.CreateModel(
            name='CertificatDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('date_expiration', models.DateField(blank=True, null=True)),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificats', to='dmct_instruments.instrumentmesure')),
            ],
            options={
                'ordering': ['-date_emission'],
            },
        ),
    ]
