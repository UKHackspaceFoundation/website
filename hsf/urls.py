from django.urls import re_path, include
from django.contrib import admin

urlpatterns = [
    re_path(r'^', include('main.urls')),
    re_path(r'^distelbot/', include('distelbot.urls')),
    re_path(r'^admin/', admin.site.urls),
]
