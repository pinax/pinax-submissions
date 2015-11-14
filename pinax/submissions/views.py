from __future__ import unicode_literals

from django.core.mail import send_mass_mail
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    HttpResponseNotAllowed
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context, Template
from django.views import static
from django.views.generic import FormView, ListView
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
    SubmissionResult,
    SupportingDocument
)
from .utils import LoggedInMixin


class SubmissionKindList(LoggedInMixin, ListView):
    """
    ListView to provide a list of submission kinds to choose from.

    """

    template_name = 'pinax/submissions/submission_submit.html'
    context_object_name = 'kinds'

    def get_queryset(self):
        return SubmissionKind.objects.all()


class SubmissionAdd(LoggedInMixin, FormView):
    template_name = 'pinax/submissions/submission_submit_kind.html'
    success_url = '/dashboard/'

    def get(self, request, *args, **kwargs):
        kind_slug = self.kwargs['kind_slug']
        form = settings.PINAX_SUBMISSIONS_FORMS[self.kwargs['kind_slug']]
        kind = get_object_or_404(SubmissionKind, slug=kind_slug)
        return render(
            request,
            self.template_name,
            {'proposal_form': form, 'kind': kind}
        )

    def post(self, request, *args, **kwargs):
        kind_slug = self.kwargs['kind_slug']
        kind = get_object_or_404(SubmissionKind, slug=kind_slug)
        form = settings.PINAX_SUBMISSIONS_FORMS[kind_slug](request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.submitter = request.user
            submission.kind = kind
            submission.save()
            form.save_m2m()
            messages.success(request, _("Submission submitted."))
            return HttpResponseRedirect(success_url)

        # @@@|TODO change this message
        messages.success(request, _("Form failed."))
        return render(request,
                      self.template_name,
                      {'proposal_form': form, 'kind': kind})


@login_required
def submission_edit(request, pk):
    submission = get_object_or_404(SubmissionBase, pk=pk)
    submission = SubmissionBase.objects.get_subclass(pk=submission.pk)

    if request.user != submission.submitter:
        raise Http404()

    if not submission.can_edit():
        ctx = {
            "title": "Submission editing closed",
            "body": "Submission editing is closed for this session type."
        }
        return render(request, "pinax/submissions/submission_error.html", ctx)

    FormClass = settings.PINAX_SUBMISSIONS_FORMS[submission.kind.slug]

    if request.method == "POST":
        form = FormClass(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            if hasattr(submission, "reviews"):
                users = User.objects.filter(
                    Q(review__submission=submission) |
                    Q(submissionmessage__submission=submission)
                )
                users = users.exclude(pk=request.user.pk).distinct()
                for user in users:
                    ctx = {
                        "user": request.user,
                        "submission": submission,
                    }
                    hookset.send_email(
                        [user.email],
                        "submission_updated",
                        context=ctx
                    )
            messages.success(request, "Submission updated.")
            return redirect("submission_detail", submission.pk)
    else:
        form = FormClass(instance=submission)

    return render(request, "pinax/submissions/submission_edit.html", {
        "submission": submission,
        "form": form,
    })


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(SubmissionBase, pk=pk, submitter=request.user)
    submission = SubmissionBase.objects.get_subclass(pk=submission.pk)

    message_form = SubmitterCommentForm()
    if request.method == "POST":
        message_form = SubmitterCommentForm(request.POST)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.user = request.user
            message.submission = submission
            message.save()

            reviewers = User.objects.filter(
                id__in=SubmissionMessage.objects.filter(
                    submission=submission
                ).exclude(
                    user=request.user
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

            return redirect(request.path)
    else:
        message_form = SubmitterCommentForm()

    return render(request, "pinax/submissions/submission_detail.html", {
        "submission": submission,
        "message_form": message_form
    })


@login_required
def submission_cancel(request, pk):
    submission = get_object_or_404(SubmissionBase, pk=pk, submitter=request.user)
    submission = SubmissionBase.objects.get_subclass(pk=submission.pk)

    if request.method == "POST":
        submission.cancel()
        # @@@ fire off email to submitter and other speakers
        messages.success(request, "Submission has been cancelled")
        return redirect("dashboard")

    return render(request, "pinax/submissions/submission_cancel.html", {
        "submission": submission,
    })


@login_required
def document_create(request, proposal_pk):
    submission = get_object_or_404(SubmissionBase, pk=proposal_pk, submitter=request.user)
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
        response = static.serve(request, document.file.name, document_root=settings.MEDIA_ROOT)
    return response


@login_required
def document_delete(request, pk):
    document = get_object_or_404(SupportingDocument, pk=pk, uploaded_by=request.user)
    if request.method == "POST":
        document.delete()
    return redirect("submission_detail", document.submission.pk)


# REVIEW VIEWS #################################################################


def access_not_permitted(request):
    return render(request, "pinax/submissions/access_not_permitted.html")


def submissions_generator(request, queryset, user_pk=None):

    for obj in queryset:
        SubmissionResult.objects.get_or_create(submission=obj)
        lookup_params = dict(submission=obj)
        if user_pk:
            lookup_params["user__pk"] = user_pk
        else:
            lookup_params["user"] = request.user
        yield obj


# Returns a list of all proposals, proposals reviewed by the user, or the proposals the user has
# yet to review depending on the link user clicks in dashboard
@login_required
def review(request, assigned=False, reviewed="all"):

    if not request.user.has_perm("reviews.can_review_submissions"):
        return access_not_permitted(request)

    queryset = SubmissionBase.objects.all()

    if assigned:
        assignments = ReviewAssignment.objects.filter(
            user=request.user
        ).values_list("proposal__id")
        queryset = queryset.filter(id__in=assignments)

    # passing reviewed in from reviews.urls and out to review_list for
    # appropriate template header rendering
    if reviewed == "all":
        queryset = queryset.select_related("result").select_subclasses()
        reviewed = "all_reviews"
    elif reviewed == "reviewed":
        queryset = queryset.filter(reviews__user=request.user)
        reviewed = "user_reviewed"
    else:
        queryset = queryset.exclude(reviews__user=request.user).exclude(submitter=request.user)
        reviewed = "user_not_reviewed"

    submissions = submissions_generator(request, queryset)

    ctx = {
        "submissions": submissions,
        "reviewed": reviewed,
    }

    return render(request, "pinax/submissions/review_list.html", ctx)


@login_required
def review_list(request, user_pk):

    # if they're not a reviewer admin and they aren't the person whose
    # review list is being asked for, don't let them in
    if not request.user.has_perm("reviews.can_manage"):
        if not request.user.pk == user_pk:
            return access_not_permitted(request)

    queryset = SubmissionBase.objects.select_related("result")
    reviewed = Review.objects.filter(user__pk=user_pk).values_list("submission", flat=True)
    queryset = queryset.filter(pk__in=reviewed)
    submissions = queryset.order_by("submitted")
    submissions = submissions_generator(request, submissions, user_pk=user_pk)

    ctx = {
        "submissions": submissions,
    }
    return render(request, "pinax/submissions/review_list.html", ctx)


@login_required
def review_admin(request):
    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    ctx = {
        "reviewers": hookset.reviewers(),
    }
    return render(request, "pinax/submissions/review_admin.html", ctx)


@login_required
def review_detail(request, pk):
    submissions = SubmissionBase.objects.select_related("result").select_subclasses()
    submission = get_object_or_404(submissions, pk=pk)

    if not request.user.has_perm("reviews.can_review"):
        return access_not_permitted(request)

    admin = request.user.is_staff

    if request.method == "POST":
        if "message_submit" in request.POST:
            message_form = SubmitterCommentForm(request.POST)
            if message_form.is_valid():
                message = message_form.save(commit=False)
                message.user = request.user
                message.submission = submission
                message.save()
                return redirect(request.path)
            else:
                initial = {}
                review_form = ReviewForm(initial=initial)
        elif "result_submit" in request.POST:
            if admin:
                result = request.POST["result_submit"]
                submission.update_result(result)
            return redirect(request.path)
    else:
        initial = {}
        review_form = ReviewForm(initial=initial)
        message_form = SubmitterCommentForm()

    reviews = Review.objects.filter(submission=submission).order_by("-submitted_at")
    messages = submission.messages.order_by("submitted_at")

    return render(request, "pinax/submissions/review_detail.html", {
        "submission": submission,
        "reviews": reviews,
        "review_messages": messages,
        "review_form": review_form,
        "message_form": message_form
    })


@login_required
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    review.delete()

    return redirect("submission_detail", pk=review.submission.pk)


@login_required
def review_assignments(request):
    if not request.user.groups.filter(name="reviewers").exists():
        return access_not_permitted(request)
    assignments = ReviewAssignment.objects.filter(
        user=request.user,
        opted_out=False
    )
    return render(request, "pinax/submissions/review_assignment.html", {
        "assignments": assignments,
    })


@login_required
@require_POST
def review_assignment_opt_out(request, pk):
    review_assignment = get_object_or_404(ReviewAssignment, pk=pk, user=request.user)
    if not review_assignment.opted_out:
        review_assignment.opted_out = True
        review_assignment.save()
        ReviewAssignment.create_assignments(review_assignment.proposal, origin=ReviewAssignment.AUTO_ASSIGNED_LATER)
    return redirect("review_assignments")

# RESULT NOTIFICATION VIEWS ####################################################

@login_required
def result_notification(request, status):
    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    submissions = SubmissionBase.objects.filter(result__status=status).select_related("result").select_subclasses()
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
        notification_template = NotificationTemplate.objects.get(pk=notification_template_pk)
    else:
        notification_template = None

    ctx = {
        "status": status,
        "notification_template": notification_template,
        "submissions": submissions,
        "submission_pks": ",".join([str(pk) for pk in submission_pks]),
    }
    return render(request, "pinax/submissions/result_notification_prepare.html", ctx)


@login_required
def result_notification_send(request, status):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.has_perm("reviews.can_manage"):
        return access_not_permitted(request)

    if not all([k in request.POST for k in ["submission_pks", "from_address", "subject", "body"]]):
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
        notification_template = NotificationTemplate.objects.get(pk=notification_template_pk)
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
