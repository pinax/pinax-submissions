import os
import uuid

from django.http import Http404
from django.views import generic


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
        if not request.user.has_perm("reviews.can_manage"):
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


def uuid_filename(instance, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join("document", filename)
