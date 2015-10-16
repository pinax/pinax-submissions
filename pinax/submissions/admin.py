from django.contrib import admin

from .models import SubmissionKind, NotificationTemplate, SubmissionResult


admin.site.register(
    NotificationTemplate,
    list_display=[
        "label",
        "from_address",
        "subject"
    ]
)
admin.site.register(
    SubmissionResult,
    list_display=["submission", "status", "accepted"]
)
admin.site.register(SubmissionKind)
