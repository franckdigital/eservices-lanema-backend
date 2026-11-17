from django.db import migrations

# Laboratoires de la Direction des Essais et Analyses (DEA), repris des
# entites de la fiche d'execution des travaux d'essais (LMP, LAI, LEE, LPI).
LABOS = [
    ("LMP", "Laboratoire de Microbiologie et de Parasitologie", "DEA", "SDCPA"),
    ("LAI", "Laboratoire de Chimie Alimentaire et Industriel", "DEA", "SDCPA"),
    ("LEE", "Laboratoire des Eaux et Environnement", "DEA", "SDCPPI"),
    ("LPI", "Laboratoire des Produits Industriels et Pétroliers", "DEA", "SDCPPI"),
]


def seed(apps, schema_editor):
    Laboratoire = apps.get_model("laboratoires", "Laboratoire")
    for code, nom, direction, sous_direction in LABOS:
        labo, created = Laboratoire.objects.get_or_create(
            code=code, defaults={"nom": nom, "direction": direction, "sous_direction": sous_direction},
        )
        if not created and not labo.direction:
            labo.direction, labo.sous_direction = direction, sous_direction
            labo.save(update_fields=["direction", "sous_direction"])


class Migration(migrations.Migration):
    dependencies = [("laboratoires", "0002_circuit_fet_rapport")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
