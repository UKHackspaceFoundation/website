from django.conf.urls import url

from . import views
from django.contrib.auth import views as authviews

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^edit-profile$', views.UserUpdate.as_view(), name='edit-profile'),
    url(r'^edit-space-profile$', views.SpaceUpdate.as_view(), name='edit-space-profile'),
    url(r'^foundation/(?P<path>.*)$', views.foundation, name='foundation'),
    url(r'^gitinfo$', views.gitinfo, name='gitinfo'),
    url(r'^home$', views.home, name='home'),
    url(r'^import_spaces$', views.import_spaces, name='import_spaces'),
    url(r'^join$', views.join, name='join'),
    url(r'^join/supporter$', views.join_supporter, name='join_supporter'),
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
]
