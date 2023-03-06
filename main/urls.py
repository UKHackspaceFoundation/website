from django.urls import re_path

from . import views
from django.contrib.auth import views as authviews
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^edit-profile$", views.UserUpdate.as_view(), name="edit-profile"),
    re_path(
        r"^edit-space-profile$", views.SpaceUpdate.as_view(), name="edit-space-profile"
    ),
    re_path(r"^error$", views.error, name="error"),
    re_path(r"^foundation/(?P<path>.*)$", views.foundation, name="foundation"),
    re_path(r"^gitinfo$", views.gitinfo, name="gitinfo"),
    re_path(
        r"^gocardless-webhook$",
        views.GocardlessWebhook.as_view(),
        name="gocardless-webhook",
    ),
    re_path(r"^profile$", views.profile, name="profile"),
    re_path(r"^import_spaces$", views.import_spaces, name="import_spaces"),
    re_path(r"^join$", views.join, name="join"),
    re_path(
        r"^join/supporter/1$",
        views.JoinSupporterStep1.as_view(),
        name="join_supporter_step1",
    ),
    re_path(r"^join/supporter/2$", views.join_supporter_step2, name="join_supporter_step2"),
    re_path(r"^join/supporter/3$", views.join_supporter_step3, name="join_supporter_step3"),
    re_path(
        r"^supporter-approval/(?P<session_token>.*)/(?P<action>.*)$",
        views.supporter_approval,
        name="supporter-approval",
    ),
    re_path(r"^login$", views.Login.as_view(), name="login"),
    re_path(r"^logout$", views.logout_view, name="logout"),
    re_path(r"^payment-history$", views.payment_history, name="payment-history"),
    re_path(r"^new-space$", views.new_space, name="new_space"),
    re_path(r"^resources/(?P<path>.*)$", views.resources, name="resources"),
    re_path(r"^signup$", views.SignupView.as_view(), name="signup"),
    re_path(r"^supporters$", views.supporters, name="supporters"),
    re_path(r"^spaces.json$", views.spaces, name="spaces"),
    re_path(r"^spaces.geojson$", views.geojson, name="geojson"),
    re_path(r"^space_detail$", views.space_detail, name="space_detail"),
    re_path(
        r"^supporter-membership-payment$",
        views.supporter_membership_payment,
        name="supporter-membership-payment",
    ),
    re_path(
        r"^signup-done/$",
        authviews.PasswordResetDoneView.as_view(
            template_name="signup/signup_done.html"
        ),
        name="signup-done",
    ),
    re_path(
        r"^signup/password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        authviews.PasswordResetConfirmView.as_view(
            template_name="password_reset/password_reset_confirm.html",
            success_url=reverse_lazy("signup-complete")
        ),
        name="password-reset-confirm",
    ),
    re_path(
        r"^signup-complete$",
        authviews.PasswordResetCompleteView.as_view(
            template_name="signup/signup_complete.html"
        ),
        name="signup-complete",
    ),
    re_path(
        r"^password-reset$",
        authviews.PasswordResetView.as_view(
            template_name="password_reset/password_reset.html",
            success_url=reverse_lazy("signup-done"),
            email_template_name="password_reset/password_reset_email.html",
            subject_template_name="password_reset/password_reset_subject.txt",
        ),
        name="password-reset",
    ),
    re_path(
        r"^space-approval/(?P<key>.*)/(?P<action>.*)$",
        views.space_approval,
        name="space-approval",
    ),
    # redirects (e.g. old urls)
    # old start-a-space view:
    re_path(
        r"^start-a-space$",
        RedirectView.as_view(
            url=reverse_lazy("resources", kwargs={"path": "start-a-space.md"})
        ),
        name="go-to-start-a-space",
    ),
    # old wiki views:
    re_path(r"view/(.*)$", RedirectView.as_view(url="/"), name="go-to-index"),
]
