from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
import uuid
from django.urls import reverse
from django import forms
import logging

# get instance of a logger
logger = logging.getLogger(__name__)


class CustomUserCreationForm(ModelForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email','first_name','last_name','space',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # override User model to ensure first and last names are required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True):
        if self.has_changed() and 'space' in self.changed_data:
            # get a reference to the user object
            user = super(CustomUserCreationForm, self).save(False)

            # reset space approval status
            user.space_status = 'Pending'

            # populate the approver email address
            # TODO: Use Representative(s) email if available
            # If space has a contact email address, then use that:
            if user.space.email != "":
                user.space_approver = user.space.email
            else:
                # otherwise use the default contact address for the site
                user.space_approver = getattr(settings, "DEFAULT_FROM_EMAIL", None)

            # note the date
            user.space_request_date = timezone.now()

            # generate a unique key for this request
            user.space_request_key = uuid.uuid4().hex

            # send approval request email
            htmly = get_template('main/space_approval_email.html')

            d = Context({
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'hackspace': user.space.name,
                'approve_url': self.request.build_absolute_uri(reverse('space-approval', kwargs={'key': user.space_request_key, 'action':'approve'} )),
                'reject_url': self.request.build_absolute_uri(reverse('space-approval', kwargs={'key': user.space_request_key, 'action':'reject'} ))
            })

            subject = "Is " + user.first_name +" " + user.last_name + " a member of " + user.space.name + "?"
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
            to = user.space_approver
            message = htmly.render(d)
            try:
                msg = EmailMessage(subject, message, to=[to], from_email=from_email)
                msg.content_subtype = 'html'
                msg.send()
            except Exception as e:
                # TODO: oh dear - how should we handle this gracefully?!?
                logger.error("Error sending space approval email: " + str(e))


        # commit changes to the DB
        return super(CustomUserCreationForm, self).save(commit)


class SupporterMemberForm(ModelForm):
    class Meta:
        model = User
        fields = ('member_fee','member_statement')

    # ensure member_fee is not less than £10.00
    def clean_member_fee(self):
        data = self.cleaned_data['member_fee']
        if data < 10:
            raise forms.ValidationError("Minimum £10.00")
        return data

    # ensure member_statement is not empty
    def clean_member_statement(self):
        data = self.cleaned_data['member_statement']
        if data == "":
            raise forms.ValidationError("Please write at least a few words :)")
        return data
