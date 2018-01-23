from django.conf.urls import include, url

urlpatterns = [
    url(r"^", include("pinax.submissions.urls", namespace="pinax_submissions")),
]
