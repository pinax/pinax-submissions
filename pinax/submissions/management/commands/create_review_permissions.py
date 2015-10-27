from django.core.management.base import BaseCommand

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):

    def handle(self, *args, **options):
        ct, created = ContentType.objects.get_or_create(
            model="",
            app_label="reviews",
            defaults={"name": "reviews"}
        )
        for action in ["review", "manage", "review_submissions"]:
            perm, created = Permission.objects.get_or_create(
                codename="can_{}".format(action),
                content_type__pk=ct.id,
                defaults={"name": "Can {}".format(action), "content_type": ct}
            )
            print(perm)
