from django.contrib import admin

from .models import Space, User, GocardlessPayment

admin.site.register(Space)
admin.site.register(User)
admin.site.register(GocardlessPayment)
