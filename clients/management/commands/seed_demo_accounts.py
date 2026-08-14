"""
Cree/reinitialise les 3 comptes de demonstration du module laboratoire.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from clients.models import ClientProfile


class Command(BaseCommand):
    help = "Cree les comptes de demonstration (client, admin, technicien)"

    def handle(self, *args, **options):
        accounts = [
            {
                "username": "client_demo",
                "email": "client@demo.com",
                "first_name": "Client",
                "last_name": "Demo",
                "role": "CLIENT",
                "organisation": "Client Demo",
                "password": "manager123",
            },
            {
                "username": "admin_demo",
                "email": "admin@demo.com",
                "first_name": "Admin",
                "last_name": "Demo",
                "role": "ADMIN",
                "organisation": "LANEMA Laboratoire",
                "is_staff": True,
                "is_superuser": True,
                "password": "admin123",
            },
            {
                "username": "technicien_demo",
                "email": "technicien@demo.com",
                "first_name": "Technicien",
                "last_name": "Demo",
                "role": "TECHNICIEN",
                "organisation": "LANEMA Laboratoire",
                "password": "manager123",
            },
        ]

        for data in accounts:
            data = dict(data)
            password = data.pop("password")
            is_superuser = data.pop("is_superuser", False)
            is_staff = data.pop("is_staff", False)
            role = data.pop("role")
            organisation = data.pop("organisation", "")

            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={**data, "is_superuser": is_superuser, "is_staff": is_staff},
            )
            if not created:
                for key, value in data.items():
                    setattr(user, key, value)
                user.is_superuser = is_superuser
                user.is_staff = is_staff
            user.set_password(password)
            user.save()

            profile, _ = ClientProfile.objects.update_or_create(
                user=user,
                defaults={"role": role, "organisation": organisation},
            )

            label = "Cree" if created else "Mis a jour"
            self.stdout.write(self.style.SUCCESS(f"[{label}] {user.email} ({profile.role})"))

        self.stdout.write(self.style.MIGRATE_HEADING("\nComptes demo disponibles :"))
        self.stdout.write("  Client      : client@demo.com / manager123")
        self.stdout.write("  Admin       : admin@demo.com / admin123")
        self.stdout.write("  Technicien  : technicien@demo.com / manager123")
