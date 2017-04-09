from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^hook$', views.hook, name='hook'),
]
