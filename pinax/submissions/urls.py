from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    "",
    url(
        r"^submit/$",
        views.SubmissionKindList.as_view(),
        name="submission_submit"
    ),
    url(
        r"^submit/(?P<kind_slug>[\w-]+)/$",
        views.SubmissionAdd.as_view(),
        name="submission_submit_kind"
    ),
    url(
        r"^(\d+)/$",
        views.submission_detail,
        name="submission_detail"
    ),
    url(
        r"^(?P<pk>\d+)/edit/$",
        views.SubmissionEdit.as_view(),
        name="submission_edit"
    ),
    url(
        r"^(\d+)/cancel/$",
        views.submission_cancel,
        name="submission_cancel"
    ),
    url(
        r"^(\d+)/document/create/$",
        views.document_create,
        name="submission_document_create"
    ),
    url(
        r"^document/(\d+)/delete/$",
        views.document_delete,
        name="submission_document_delete"
    ),
    url(
        r"^document/(\d+)/([^/]+)$",
        views.document_download,
        name="submission_document_download"
    ),

    url(
        r"^all/$",
        views.review,
        {"reviewed": "all"},
        name="review_section"
    ),
    url(
        r"^reviewed/$",
        views.review,
        {"reviewed": "reviewed"},
        name="user_reviewed"
    ),
    url(
        r"^not-reviewed/$",
        views.review,
        {"reviewed": "not_reviewed"},
        name="user_not_reviewed"
    ),
    url(
        r"^assignments/$",
        views.review,
        {"assigned": True},
        name="review_section_assignments"
    ),
    url(
        r"^list/(?P<user_pk>\d+)/$",
        views.ReviewList.as_view(),
        name="review_list_user"
    ),
    url(
        r"^admin/$",
        views.ReviewAdmin.as_view(),
        name="review_admin"
    ),
    url(
        r"^notification/(?P<status>\w+)/$",
        views.result_notification,
        name="result_notification"
    ),
    url(
        r"^notification/(?P<status>\w+)/prepare/$",
        views.result_notification_prepare,
        name="result_notification_prepare"
    ),
    url(
        r"^notification/(?P<status>\w+)/send/$",
        views.result_notification_send,
        name="result_notification_send"
    ),
    url(
        r"^reviews/(?P<pk>\d+)/$",
        views.review_detail,
        name="review_detail"
    ),

    url(
        r"^reviews(?P<pk>\d+)/delete/$",
        views.review_delete,
        name="review_delete"
    ),
    url(
        r"^assignments/$",
        views.review_assignments,
        name="review_assignments"
    ),
    url(
        r"^assignment/(?P<pk>\d+)/opt-out/$",
        views.review_assignment_opt_out,
        name="review_assignment_opt_out"
    ),
)
