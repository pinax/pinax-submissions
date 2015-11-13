import os
import uuid

from django.views import generic


class LoggedInMixin(object):
    """
    A mixin requiring a user to be logged in.

    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise http.Http404
        self.kwargs = kwargs
        return super(LoggedInMixin, self).dispatch(request, *args, **kwargs)


def uuid_filename(instance, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join("document", filename)
