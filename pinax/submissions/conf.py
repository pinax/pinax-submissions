from __future__ import unicode_literals

from importlib import import_module

from django.conf import settings  # noqa
from django.core.exceptions import ImproperlyConfigured

from appconf import AppConf


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured("Error importing %s: '%s'" % (module, e))
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured("Module '%s' does not define a '%s'" % (module, attr))
    return attr


class PinaxPagesAppConf(AppConf):

    HOOKSET = "pinax.submissions.hooks.DefaultHookSet"
    MARKUP_RENDERER = "markdown.markdown"
    FORMS = {}

    def configure_markup_renderer(self, value):
        return load_path_attr(value)

    def configure_hookset(self, value):
        return load_path_attr(value)()

    def configure_forms(self, value):
        forms = {}
        for k, v in value.items():
            forms[k] = load_path_attr(v)
        return forms

    class Meta:
        prefix = "pinax_submissions"
