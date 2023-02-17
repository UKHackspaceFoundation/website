from django.conf.urls import url

from . import views
from django.contrib.auth import views as authviews
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy

urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^edit-profile$", views.UserUpdate.as_view(), name="edit-profile"),
    url(
        r"^edit-space-profile$", views.SpaceUpdate.as_view(), name="edit-space-profile"
    ),
    url(r"^error$", views.error, name="error"),
    url(r"^foundation/(?P<path>.*)$", views.foundation, name="foundation"),
    url(r"^gitinfo$", views.gitinfo, name="gitinfo"),
    url(
        r"^gocardless-webhook$",
        views.GocardlessWebhook.as_view(),
        name="gocardless-webhook",
    ),
    url(r"^profile$", views.profile, name="profile"),
    url(r"^import_spaces$", views.import_spaces, name="import_spaces"),
    url(r"^join$", views.join, name="join"),
    url(
        r"^join/supporter/1$",
        views.JoinSupporterStep1.as_view(),
        name="join_supporter_step1",
    ),
    url(r"^join/supporter/2$", views.join_supporter_step2, name="join_supporter_step2"),
    url(r"^join/supporter/3$", views.join_supporter_step3, name="join_supporter_step3"),
    url(
        r"^supporter-approval/(?P<session_token>.*)/(?P<action>.*)$",
        views.supporter_approval,
        name="supporter-approval",
    ),
    url(r"^login$", views.Login.as_view(), name="login"),
    url(r"^logout$", views.logout_view, name="logout"),
    url(r"^payment-history$", views.payment_history, name="payment-history"),
    url(r"^new-space$", views.new_space, name="new_space"),
    url(r"^resources/(?P<path>.*)$", views.resources, name="resources"),
    url(r"^signup$", views.SignupView.as_view(), name="signup"),
    url(r"^supporters$", views.supporters, name="supporters"),
    url(r"^spaces.json$", views.spaces, name="spaces"),
    url(r"^spaces.geojson$", views.geojson, name="geojson"),
    url(r"^space_detail$", views.space_detail, name="space_detail"),
    url(
        r"^supporter-membership-payment$",
        views.supporter_membership_payment,
        name="supporter-membership-payment",
    ),
    url(
        r"^signup-done/$",
        authviews.PasswordResetDoneView.as_view(
            template_name="signup/signup_done.html"
        ),
        name="signup-done",
    ),
    url(
        r"^signup/password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        authviews.PasswordResetConfirmView.as_view(
            template_name="password_reset/password_reset_confirm.html",
            success_url=reverse_lazy("signup-complete")
        ),
        name="password-reset-confirm",
    ),
    url(
        r"^signup-complete$",
        authviews.PasswordResetCompleteView.as_view(
            template_name="signup/signup_complete.html"
        ),
        name="signup-complete",
    ),
    url(
        r"^password-reset$",
        authviews.PasswordResetView.as_view(
            template_name="password_reset/password_reset.html",
            success_url=reverse_lazy("signup-done"),
            email_template_name="password_reset/password_reset_email.html",
            subject_template_name="password_reset/password_reset_subject.txt",
        ),
        name="password-reset",
    ),
    url(
        r"^space-approval/(?P<key>.*)/(?P<action>.*)$",
        views.space_approval,
        name="space-approval",
    ),
    # redirects (e.g. old urls)
    # old start-a-space view:
    url(
        r"^start-a-space$",
        RedirectView.as_view(
            url=reverse_lazy("resources", kwargs={"path": "start-a-space.md"})
        ),
        name="go-to-start-a-space",
    ),
    # old wiki views:
    url(r"view/(.*)$", RedirectView.as_view(url="/"), name="go-to-index"),
]
