from django.http import Http404
from django.shortcuts import render

from .models import SubmissionResult


class LoggedInMixin(object):
    """
    A mixin requiring a user to be logged in.
    If the user is not authenticated, show the 404 page.

    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        return super(LoggedInMixin, self).dispatch(request, *args, **kwargs)


class CanReviewMixin(object):
    """
    Mixin that checks the user's permissions to manage review as a reviewer
    admin or their review list

    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("reviews.can_review_submissions"):
            if not request.user.pk == self.kwargs['user_pk']:
                render(request, "pinax/submissions/access_not_permitted.html")
        return super(CanReviewMixin, self).dispatch(request, *args, **kwargs)


class CanManageMixin(object):
    """
    Mixin to ensure user can manage reviews

    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("reviews.can_manage"):
            render(request, "pinax/submissions/access_not_permitted.html")
        return super(CanManageMixin, self).dispatch(request, *args, **kwargs)


def submissions_generator(request, queryset, user_pk=None):
    for obj in queryset:
        SubmissionResult.objects.get_or_create(submission=obj)
        lookup_params = dict(submission=obj)
        if user_pk:
            lookup_params["user__pk"] = user_pk
        else:
            lookup_params["user"] = request.user
        yield obj
