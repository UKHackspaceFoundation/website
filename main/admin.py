from django.contrib import admin

from .models import User, Space, SupporterMembership, SpaceMembership, GocardlessMandate, GocardlessPayment

admin.site.register(User)
admin.site.register(Space)
admin.site.register(SupporterMembership)
admin.site.register(SpaceMembership)
admin.site.register(GocardlessMandate)
admin.site.register(GocardlessPayment)
