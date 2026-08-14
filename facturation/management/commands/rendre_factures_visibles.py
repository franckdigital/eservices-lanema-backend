from django.core.management.base import BaseCommand
from facturation.models import Facture


class Command(BaseCommand):
    help = "Rend toutes les factures existantes visibles aux clients"

    def handle(self, *args, **options):
        factures = Facture.objects.filter(visible_client=False)
        count = factures.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("Aucune facture à mettre à jour. Toutes les factures sont déjà visibles.")
            )
            return
        
        factures.update(visible_client=True)
        
        self.stdout.write(
            self.style.SUCCESS(f"{count} facture(s) ont été rendues visibles aux clients.")
        )
