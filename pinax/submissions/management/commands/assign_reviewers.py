from django.core.management.base import BaseCommand

from ..models import ReviewAssignment, SubmissionBase


class Command(BaseCommand):

    def handle(self, *args, **options):
        for submission in SubmissionBase.objects.filter(cancelled=False):
            print(f"Creating assignments for {submission}")
            ReviewAssignment.create_assignments(submission)
