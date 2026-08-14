# Fusionne une branche orpheline de longue date : 0100_direction_type_userprofile_cabinet_dg
# n'avait jamais ete rattachee a la chaine principale (elle partageait le meme
# numero de sequence que 0100_add_rappel_traitement_to_courrier, cree en parallele).
# Ses champs (Direction.type_direction, UserProfile.cabinet/direction_generale)
# sont deja utilises partout dans le code, donc deja appliques en base sur tout
# environnement fonctionnel : cette migration ne fait que reconcilier l'historique,
# aucune operation de schema.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0100_direction_type_userprofile_cabinet_dg'),
        ('core', '0114_fiche_agent_depart'),
    ]

    operations = [
    ]
