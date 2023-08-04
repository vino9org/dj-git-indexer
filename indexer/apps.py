import secrets
import string

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for i in range(length))


def check_superuser(sender, **kwargs):
    from django.contrib.auth.models import User

    if User.objects.filter(is_superuser=True).exists():
        print("post_migrate: superuser exists.")
        return

    username = "admin"
    email = "admin@git.com"
    password = generate_random_password()

    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"post_migrate:  Superuser created with username: {username}, password: {password}")


class IndexerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "indexer"

    def ready(self):
        post_migrate.connect(check_superuser, sender=self)
