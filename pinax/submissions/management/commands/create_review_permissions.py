from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        ct, created = ContentType.objects.get_or_create(
            model="",
            app_label="reviews",
            defaults={"name": "reviews"}
        )
        for action in ["review", "manage", "review_submissions"]:
            perm, created = Permission.objects.get_or_create(
                codename=f"can_{action}",
                content_type__pk=ct.id,
                defaults={"name": f"Can {action}", "content_type": ct}
            )
            print(perm)
