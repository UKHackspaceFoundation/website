from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^start-a-space$', views.starting, name='starting'),
    url(r'^join', views.join, name='join'),
    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
]
