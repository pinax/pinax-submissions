from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site


class DefaultHookSet(object):

    def __init__(self):
        from .conf import settings  # if put globally there is a race condition
        self.settings = settings

    def reviewers(self):
        perm = Permission.objects.get(codename="reviews.can_review")
        return User.objects.filter(
            Q(groups__permissions=perm) | Q(user_permissions=perm)
        ).distinct()

    def parse_content(self, content):
        return self.settings.PINAX_SUBMISSIONS_MARKUP_RENDERER(content)

    def send_email(self, to, kind, **kwargs):
        current_site = Site.objects.get_current()
        ctx = {
            "current_site": current_site,
            "STATIC_URL": self.settings.STATIC_URL,
        }
        ctx.update(kwargs.get("context", {}))
        subject = "[%s] %s" % (
            current_site.name,
            render_to_string("pinax/submissions/emails/%s/subject.txt" % kind, ctx).strip()
        )

        message_html = render_to_string("pinax/submission/emails/%s/message.html" % kind, ctx)
        message_plaintext = strip_tags(message_html)

        from_email = self.settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(subject, message_plaintext, from_email, to)
        email.attach_alternative(message_html, "text/html")
        email.send()


class HookProxy(object):

    def __getattr__(self, attr):
        from .conf import settings  # if put globally there is a race condition
        return getattr(settings.PINAX_SUBMISSIONS_HOOKSET, attr)


hookset = HookProxy()
