from __future__ import unicode_literals

from django.core.mail import send_mass_mail
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context, Template
from django.views import static
from django.views.generic import (
    ListView,
    UpdateView,
    FormView,
    DetailView,
    DeleteView
)
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _

from account.decorators import login_required

from .conf import settings
from .forms import (
    ReviewForm,
    SubmitterCommentForm,
    SupportingDocumentCreateForm
)
from .hooks import hookset
from .models import (
    NotificationTemplate,
    ResultNotification,
    Review,
    ReviewAssignment,
    SubmissionBase,
    SubmissionKind,
    SubmissionMessage,
    SupportingDocument
)
from .utils import (
    LoggedInMixin,
    CanReviewMixin,
    submissions_generator
)


class SubmissionKindList(LoggedInMixin, ListView):
    """
    ListView to provide a list of submission kinds to choose from.

    """

    template_name = "pinax/submissions/submission_submit.html"
    context_object_name = "kinds"

    def get_queryset(self):
        return SubmissionKind.objects.all()


class SubmissionAdd(LoggedInMixin, FormView):
    template_name = "pinax/submissions/submission_submit_kind.html"
    success_url = "/dashboard/"

    def get_form_class(self):
        return settings.PINAX_SUBMISSIONS_FORMS[self.kwargs["kind_slug"]]

    def get_context_data(self, **kwargs):
        kind_slug = self.kwargs["kind_slug"]
        kind = get_object_or_404(SubmissionKind, slug=kind_slug)

        return super(SubmissionAdd, self).get_context_data(
            kind=kind,
            kind_slug=kind_slug,
            proposal_form=self.get_form_class(),
            **kwargs)

    def form_valid(self, form):
        ctx = self.get_context_data()
        submission = form.save(commit=False)
        submission.submitter = self.request.user
        submission.kind = ctx.get("kind")
        submission.save()
        form.save_m2m()
        messages.success(self.request, _("Submission submitted."))
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        # @@@|TODO change this message
        messages.success(self.request, _("Form failed."))
        context = self.get_context_data()
        context["proposal_form"] = form
        return self.render_to_response(context)


class SubmissionEdit(LoggedInMixin, UpdateView):

    template_name = "pinax/submissions/submission_edit.html"
    # @@@|TODO change url
    success_url = "/dashboard/"

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        submission = get_object_or_404(SubmissionBase, pk=pk)
        submission = SubmissionBase.objects.get_subclass(pk=submission.pk)

        if self.request.user != submission.submitter:
            raise Http404()

        if not submission.can_edit():
            ctx = {
                "title": "Submission editing closed",
                "body": "Submission editing is closed for this session type."
            }
            return render(
                self.request,
                "pinax/submissions/submission_error.html",
                ctx
            )
        return submission

    def get_form_class(self):
        return settings.PINAX_SUBMISSIONS_FORMS[self.get_object().kind.slug]

    def get_context_data(self, **kwargs):
        return super(SubmissionEdit, self).get_context_data(
            submission=self.get_object(),
            **kwargs)

    def form_valid(self, form):
        submission = self.get_object()
        form.save()
        if hasattr(submission, "reviews"):
            users = User.objects.filter(
                Q(review__submission=submission) |
                Q(submissionmessage__submission=submission)
            )
            users = users.exclude(pk=self.request.user.pk).distinct()
            for user in users:
                ctx = {
                    "user": self.request.user,
                    "submission": submission,
                }
                hookset.send_email(
                    [user.email],
                    "submission_updated",
                    context=ctx
                )
        messages.success(self.request, "Submission updated.")
        return HttpResponseRedirect(self.success_url)


class SubmissionDetail(LoggedInMixin, DetailView):

    template_name = "pinax/submissions/submission_detail.html"

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        submission = get_object_or_404(
            SubmissionBase,
            pk=pk,
            submitter=self.request.user
        )
        submission = SubmissionBase.objects.get_subclass(pk=submission.pk)
        return submission

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SubmitterCommentForm(self.request.POST)

        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        submission = self.get_object()
        message = form.save(commit=False)
        message.user = self.request.user
        message.submission = submission
        message.save()

        reviewers = User.objects.filter(
            id__in=SubmissionMessage.objects.filter(
                submission=submission
            ).exclude(
                user=self.request.user
            ).distinct().values_list("user", flat=True)
        )

        for reviewer in reviewers:
            ctx = {
                "submission": submission,
                "message": message,
                "reviewer": True,
            }
            hookset.send_email(
                [reviewer.email],
                "submission_new_message",
                context=ctx
            )

        return redirect(self.request.path)

    def form_invalid(self, form):
        messages.success(self.request, _("Comment Form failed."))
        return self.render_to_response(
            self.get_context_data(message_form=form))

    def get_context_data(self, **kwargs):
        context = super(SubmissionDetail, self).get_context_data(**kwargs)
        self.object = self.get_object()
        context["submission"] = self.object
        context["message_form"] = SubmitterCommentForm(instance=self.object)
        return context


class SubmissionCancel(LoggedInMixin, DetailView):

    template_name = "pinax/submissions/submission_cancel.html"

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        submission = get_object_or_404(
            SubmissionBase,
            pk=pk,
            submitter=self.request.user
        )
        submission = SubmissionBase.objects.get_subclass(pk=submission.pk)
        return submission

    def post(self, request, *args, **kwargs):
        submission = self.get_object()
        submission.cancel()
        # @@@|TODO fire off email to submitter and other speakers
        messages.success(request, "Submission has been cancelled")
        return redirect("dashboard")

    def get_context_data(self, **kwargs):
        context = super(SubmissionCancel, self).get_context_data(**kwargs)
        self.object = self.get_object()
        context["submission"] = self.object
        return context


# REVIEW VIEWS ################################################################


def access_not_permitted(request):
    return render(request, "pinax/submissions/access_not_permitted.html")


class Reviews(LoggedInMixin, CanReviewMixin, ListView):
    """
    Returns a list of all proposals, proposals reviewed by the user, or the
    proposals the user has yet to review depending on the link user clicks in
    dashboard

    """

    template_name = "pinax/submissions/review_list.html"
    assigned = False
    reviewed = "all"
    context_object_name = "submissions"
    queryset = SubmissionBase.objects.all()

    def get_context_data(self, **kwargs):
        context = super(Reviews, self).get_context_data(**kwargs)
        queryset = self.queryset

        if self.assigned:
            assignments = ReviewAssignment.objects.filter(
                user=self.request.user
            ).values_list("submission__id")
            queryset = queryset.filter(id__in=assignments)

        # passing reviewed in from reviews.urls and out to review_list for
        # appropriate template header rendering
        if self.reviewed == "all":
            queryset = queryset.select_related("result").select_subclasses()
            reviewed = "all_reviews"
        elif self.reviewed == "reviewed":
            queryset = queryset.filter(reviews__user=self.request.user)
            reviewed = "user_reviewed"
        else:
            queryset = queryset.exclude(
                reviews__user=self.request.user).exclude(submitter=self.request.user)
            reviewed = "user_not_reviewed"

        submissions = submissions_generator(self.request, queryset)

        context["reviewed"] = reviewed
        context["submissions"] = submissions

        return context


class ReviewList(LoggedInMixin, CanReviewMixin, ListView):

    template_name = "pinax/submissions/review_list.html"
    context_object_name = "submissions"

    def get_queryset(self):
        queryset = SubmissionBase.objects.select_related("result")
        reviewed = Review.objects.filter(
            user__pk=self.kwargs["user_pk"]
        ).values_list("submission", flat=True)
        queryset = queryset.filter(pk__in=reviewed)
        submissions = queryset.order_by("submitted")
        submissions = submissions_generator(
            self.request,
            submissions,
            user_pk=self.kwargs["user_pk"]
        )

        return submissions


class ReviewAdmin(LoggedInMixin, CanReviewMixin, ListView):

    template_name = "pinax/submissions/review_admin.html"
    context_object_name = "reviewers"

    def get_queryset(self):
        return hookset.reviewers()


class ReviewDetail(LoggedInMixin, CanReviewMixin, DetailView):

    template_name = "pinax/submissions/review_detail.html"

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        submissions = SubmissionBase.objects.\
            select_related("result").select_subclasses()
        submission = get_object_or_404(submissions, pk=pk)
        return submission

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        admin = self.request.user.is_staff
        message_form = SubmitterCommentForm(self.request.POST)
        if "message_submit" in request.POST:
            if message_form.is_valid():
                return self.form_valid(message_form)
        elif "result_submit" in request.POST:
            if admin:
                result = request.POST["result_submit"]
                self.object.update_result(result)
            return redirect(request.path)

    def form_valid(self, form):
        message = form.save(commit=False)
        message.user = self.request.user
        message.submission = self.object
        message.save()
        return redirect(self.request.path)

    def form_invalid(self, form):
        initial = {}
        review_form = ReviewForm(initial=initial)
        return self.render_to_response(
            self.get_context_data(review_form=review_form))

    def get_context_data(self, **kwargs):
        context = super(ReviewDetail, self).get_context_data(**kwargs)
        submission = self.get_object()
        reviews = Review.objects.filter(
            submission=submission).order_by("-submitted_at")
        messages = submission.messages.order_by("submitted_at")

        context["submission"] = submission
        context["reviews"] = reviews
        context["review_messages"] = messages
        context["review_form"] = ReviewForm(initial={})
        context["message_form"] = SubmitterCommentForm()
        return context


class ReviewDelete(LoggedInMixin, CanReviewMixin, DeleteView):
    model = Review
    success_url = "submission_detail"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url, pk=self.object.submission.pk)


class ReviewAssignments(LoggedInMixin, CanReviewMixin, DetailView):

    template_name = "pinax/submissions/review_assignment.html"
    context_object_name = "assignments"

    def get_queryset(self):
        assignments = ReviewAssignment.objects.filter(
            user=self.request.user,
            opted_out=False
        )
        return assignments


@login_required
@require_POST
def review_assignment_opt_out(request, pk):
    review_assignment = get_object_or_404(
        ReviewAssignment,
        pk=pk,
        user=request.user
    )
    if not review_assignment.opted_out:
        review_assignment.opted_out = True
        review_assignment.save()
        ReviewAssignment.create_assignments(
            review_assignment.proposal,
            origin=ReviewAssignment.AUTO_ASSIGNED_LATER
        )
    return redirect("review_assignments")


# RESULT NOTIFICATION VIEWS ###################################################


@login_required
def result_notification(request, status):
    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    submissions = SubmissionBase.objects.filter(
        result__status=status).select_related("result").select_subclasses()
    notification_templates = NotificationTemplate.objects.all()

    ctx = {
        "status": status,
        "submissions": submissions,
        "notification_templates": notification_templates,
    }
    return render(request, "pinax/submissions/result_notification.html", ctx)


@login_required
def result_notification_prepare(request, status):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    submission_pks = []
    try:
        for pk in request.POST.getlist("_selected_action"):
            submission_pks.append(int(pk))
    except ValueError:
        return HttpResponseBadRequest()
    submissions = SubmissionBase.objects.filter(
        result__status=status,
    )
    submissions = submissions.filter(pk__in=submission_pks)
    submissions = submissions.select_related("result")
    submissions = submissions.select_subclasses()

    notification_template_pk = request.POST.get("notification_template", "")
    if notification_template_pk:
        notification_template = NotificationTemplate.objects.get(
            pk=notification_template_pk)
    else:
        notification_template = None

    ctx = {
        "status": status,
        "notification_template": notification_template,
        "submissions": submissions,
        "submission_pks": ",".join([str(pk) for pk in submission_pks]),
    }
    return render(
        request,
        "pinax/submissions/result_notification_prepare.html",
        ctx
    )


@login_required
def result_notification_send(request, status):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    if not all([k in request.POST for k in ["submission_pks", "from_address",
                                            "subject", "body"]]):
        return HttpResponseBadRequest()

    try:
        submission_pks = [int(pk) for pk in request.POST["submission_pks"].split(",")]
    except ValueError:
        return HttpResponseBadRequest()

    submissions = SubmissionBase.objects.filter(
        result__status=status,
    )
    submissions = submissions.filter(pk__in=submission_pks)
    submissions = submissions.select_related("result")
    submissions = submissions.select_subclasses()

    notification_template_pk = request.POST.get("notification_template", "")
    if notification_template_pk:
        notification_template = NotificationTemplate.objects.get(
            pk=notification_template_pk)
    else:
        notification_template = None

    emails = []

    for submission in submissions:
        rn = ResultNotification()
        rn.submission = submission
        rn.template = notification_template
        rn.to_address = submission.submitter.email
        rn.from_address = request.POST["from_address"]
        rn.subject = request.POST["subject"]
        rn.body = Template(request.POST["body"]).render(
            Context({
                "submission": submission.notification_email_context()
            })
        )
        rn.save()
        emails.append(rn.email_args)

    send_mass_mail(emails)

    return redirect("result_notification", status=status)


# DOCUMENT VIEWS #############################################################
# @@@|TODO write class-based views for these

@login_required
def document_create(request, proposal_pk):
    submission = get_object_or_404(
        SubmissionBase,
        pk=proposal_pk,
        submitter=request.user
    )
    submission = SubmissionBase.objects.get_subclass(pk=submission.pk)

    if submission.cancelled:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = SupportingDocumentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.submission = submission
            document.uploaded_by = request.user
            document.save()
            return redirect("submission_detail", submission.pk)
    else:
        form = SupportingDocumentCreateForm()

    return render(request, "pinax/submissions/document_create.html", {
        "submission": submission,
        "form": form,
    })


@login_required
def document_download(request, pk, *args):
    document = get_object_or_404(SupportingDocument, pk=pk)
    if getattr(settings, "USE_X_ACCEL_REDIRECT", False):
        response = HttpResponse()
        response["X-Accel-Redirect"] = document.file.url
        # delete content-type to allow Gondor to determine the filetype and
        # we definitely don't want Django's crappy default :-)
        del response["content-type"]
    else:
        response = static.serve(
            request,
            document.file.name,
            document_root=settings.MEDIA_ROOT
        )
    return response


@login_required
def document_delete(request, pk):
    document = get_object_or_404(
        SupportingDocument,
        pk=pk,
        uploaded_by=request.user
    )
    if request.method == "POST":
        document.delete()
    return redirect("submission_detail", document.submission.pk)
