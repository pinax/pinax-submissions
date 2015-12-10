# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from model_utils.managers import InheritanceManager

from .hooks import hookset


def uuid_filename(instance, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join("document", filename)


@python_2_unicode_compatible
class SubmissionKind(models.Model):
    """
    e.g. talk vs panel vs tutorial vs poster
    """
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(verbose_name=_("Slug"))

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class SubmissionBase(models.Model):

    kind = models.ForeignKey(SubmissionKind, verbose_name=_("Kind"))
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL)
    submitted = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("Submitted")
    )
    cancelled = models.BooleanField(default=False, verbose_name=_("Cancelled"))

    objects = InheritanceManager()

    def cancel(self):
        self.cancelled = True
        self.save()

    def update_result(self, result):
        if result == "accept":
            self.accept()
        elif result == "reject":
            self.reject()
        elif result == "undecide":
            self.undecide()
        elif result == "standby":
            self.standby()

    def accept(self):
        self.result.status = "accepted"
        self.result.save()

    def reject(self):
        self.result.status = "rejected"
        self.result.save()

    def undecide(self):
        self.result.status = "undecided"
        self.result.save()

    def standby(self):
        self.result.status = "standby"
        self.result.save()

    def can_edit(self):
        return True

    @property
    def number(self):
        return str(self.pk).zfill(3)

    @property
    def status(self):
        try:
            return self.result.status
        except ObjectDoesNotExist:
            return _("Undecided")

    def notification_email_context(self):
        return {
            "kind": self.kind.name,
        }

    def __str__(self):
        return "<Submission pk={}, kind={}>".format(self.pk, self.kind)


class SupportingDocument(models.Model):
    submission = models.ForeignKey(SubmissionBase, related_name="supporting_documents", verbose_name=_("Submission"))
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("Uploaded by"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Created at"))
    document = models.FileField(upload_to=uuid_filename, verbose_name=_("Document"))
    description = models.CharField(max_length=140, verbose_name=_("Description"))

    def download_url(self):
        return reverse("submissions_document_download", args=[self.pk, os.path.basename(self.file.name).lower()])


class ReviewAssignment(models.Model):
    AUTO_ASSIGNED_INITIAL = 0
    OPT_IN = 1
    AUTO_ASSIGNED_LATER = 2

    NUM_REVIEWERS = 3

    ORIGIN_CHOICES = [
        (AUTO_ASSIGNED_INITIAL, _("auto-assigned, initial")),
        (OPT_IN, _("opted-in")),
        (AUTO_ASSIGNED_LATER, _("auto-assigned, later")),
    ]

    submission = models.ForeignKey(SubmissionBase, verbose_name=_("Submission"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"))
    origin = models.IntegerField(choices=ORIGIN_CHOICES, verbose_name=_("Origin"))
    assigned_at = models.DateTimeField(default=timezone.now, verbose_name=_("Assigned at"))
    opted_out = models.BooleanField(default=False, verbose_name=_("Opted out"))

    @classmethod
    def create_assignments(cls, submission, origin=AUTO_ASSIGNED_INITIAL):
        hookset.create_assignments(cls, submission, origin)


class SubmissionMessage(models.Model):
    submission = models.ForeignKey(SubmissionBase, related_name="messages", verbose_name=_("Submission"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"))
    message = models.TextField(verbose_name=_("Message"))
    message_html = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_("Submitted at"))

    def save(self, *args, **kwargs):
        self.message_html = hookset.parse_content(self.message)
        return super(SubmissionMessage, self).save(*args, **kwargs)

    class Meta:
        ordering = ["submitted_at"]
        verbose_name = _("submission message")
        verbose_name_plural = _("submission messages")


class Review(models.Model):
    submission = models.ForeignKey(SubmissionBase, related_name="reviews", verbose_name=_("Submission"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"))
    comment = models.TextField(verbose_name=_("Comment"))
    comment_html = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_("Submitted at"))

    def save(self, **kwargs):
        self.comment_html = hookset.parse_content(self.comment)
        super(Review, self).save(**kwargs)

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")


class SubmissionResult(models.Model):
    submission = models.OneToOneField(SubmissionBase, related_name="result", verbose_name=_("Submission"))
    accepted = models.NullBooleanField(choices=[
        (True, "accepted"),
        (False, "rejected"),
        (None, "undecided"),
    ], default=None, verbose_name=_("Accepted"))
    status = models.CharField(max_length=20, choices=[
        ("accepted", _("accepted")),
        ("rejected", _("rejected")),
        ("undecided", _("undecided")),
        ("standby", _("standby")),
    ], default="undecided", verbose_name=_("Status"))

    @property
    def accepted(self):
        return self.status == "accepted"

    @property
    def comment_count(self):
        self.submssion.reviews.count()

    class Meta:
        verbose_name = _("submission result")
        verbose_name_plural = _("submission results")


class Comment(models.Model):
    submission = models.ForeignKey(SubmissionBase, related_name="comments", verbose_name=_("Submission"))
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("Commenter"))
    text = models.TextField(verbose_name=_("Text"))
    text_html = models.TextField(blank=True)

    # Or perhaps more accurately, can the user see this comment.
    public = models.BooleanField(choices=[(True, _("public")), (False, _("private"))], default=False, verbose_name=_("Public"))
    commented_at = models.DateTimeField(default=timezone.now, verbose_name=_("Commented at"))

    class Meta:
        verbose_name = _("comment")
        verbose_name_plural = _("comments")

    def save(self, *args, **kwargs):
        self.comment_html = hookset.parse_content(self.comment)
        return super(Comment, self).save(*args, **kwargs)


class NotificationTemplate(models.Model):
    label = models.CharField(max_length=100, verbose_name=_("Label"))
    from_address = models.EmailField(verbose_name=_("From address"))
    subject = models.CharField(max_length=100, verbose_name=_("Subject"))
    body = models.TextField(verbose_name=_("Body"))

    class Meta:
        verbose_name = _("notification template")
        verbose_name_plural = _("notification templates")


class ResultNotification(models.Model):
    submission = models.ForeignKey(SubmissionBase, related_name="notifications", verbose_name=_("Submission"))
    template = models.ForeignKey(NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Template"))
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_("Timestamp"))
    to_address = models.EmailField(verbose_name=_("To address"))
    from_address = models.EmailField(verbose_name=_("From address"))
    subject = models.CharField(max_length=100, verbose_name=_("Subject"))
    body = models.TextField(verbose_name=_("Body"))

    def email_args(self):
        return (self.subject, self.body, self.from_address, self.recipients())
