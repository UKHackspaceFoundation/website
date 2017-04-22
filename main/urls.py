from django.conf.urls import url

from . import views
from django.contrib.auth import views as authviews

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^edit-profile$', views.UserUpdate.as_view(), name='edit-profile'),
    url(r'^edit-space-profile$', views.SpaceUpdate.as_view(), name='edit-space-profile'),
    url(r'^foundation/(?P<path>.*)$', views.foundation, name='foundation'),
    url(r'^gitinfo$', views.gitinfo, name='gitinfo'),
    url(r'^profile$', views.profile, name='profile'),
    url(r'^import_spaces$', views.import_spaces, name='import_spaces'),
    url(r'^join$', views.join, name='join'),
    url(r'^join/supporter/1$', views.join_supporter_step1.as_view(), name='join_supporter_step1'),
    url(r'^join/supporter/2$', views.join_supporter_step2, name='join_supporter_step2'),
    url(r'^join/supporter/3/(?P<session_token>[0-9A-Za-z_\-]+)$', views.join_supporter_step3, name='join_supporter_step3'),
    url(r'^supporter-approval/(?P<session_token>.*)/(?P<action>.*)$', views.supporter_approval, name='supporter-approval'),
    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^resources/(?P<path>.*)$', views.resources, name='resources'),
    url(r'^signup$', views.SignupView.as_view(), name='signup'),
    url(r'^spaces.json$', views.spaces, name='spaces'),
    url(r'^spaces.geojson$', views.geojson, name='geojson'),
    url(r'^space_detail$', views.space_detail, name='space_detail'),
    url(r'^start-a-space$', views.starting, name='starting'),

    url(r'^signup-done/$', authviews.password_reset_done, {
        'template_name': 'main/signup_done.html',
    }, name='signup-done'),
    url(r'^signup/password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', authviews.password_reset_confirm, {
        'template_name': 'main/password_reset_confirm.html',
        'post_reset_redirect': 'signup-complete',
    }, name='password-reset-confirm'),
    url(r'^signup-complete$', authviews.password_reset_complete, {
        'template_name': 'main/signup_complete.html',
    }, name='signup-complete'),
    url(r'^password-reset$', authviews.password_reset, {
        'template_name': 'main/password_reset.html',
        'post_reset_redirect': 'signup-done',
        'email_template_name': 'main/password_reset_email.html',
        'subject_template_name': 'main/password_reset_subject.txt'
    }, name='password-reset'),

    url(r'^space-approval/(?P<key>.*)/(?P<action>.*)$', views.space_approval, name='space-approval'),
]
