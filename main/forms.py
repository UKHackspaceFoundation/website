from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User, SupporterMembership
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings
import uuid
from django.urls import reverse
from django import forms
import logging

# get instance of a logger
logger = logging.getLogger(__name__)


class CustomUserCreationForm(ModelForm):
    # insert a field to indicate approval to Code of Conduct, defaults to false
    agree_to_coc = forms.BooleanField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name', 'space', 'agree_to_coc')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # override User model to ensure first and last names are required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # check if user is active, if active, then disable the coc field
        if hasattr(self.request.user, 'active') and self.request.user.active:
            del self.fields['agree_to_coc']

    # Add validation to ensure agreement to code of conduct
    def clear_agree_to_coc(self):
        data = self.cleaned_data['agree_to_coc']
        if not data:
            raise forms.ValidationError("You must agree to the Code of Conduct to register")
        return data

    def save(self, commit=True):
        if self.has_changed() and 'space' in self.changed_data:
            # get a reference to the user object
            user = super(CustomUserCreationForm, self).save(False)

            # see if user has selected None
            if user.space is None:
                # reset space status
                user.space_status = 'Blank'

            else:
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
                htmly = get_template('user_space_verification/space_approval_email.html')

                d = {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'hackspace': user.space.name,
                    'approve_url': self.request.build_absolute_uri(
                        reverse('space-approval',
                                kwargs={'key': user.space_request_key, 'action': 'approve'})),
                    'reject_url': self.request.build_absolute_uri(
                        reverse('space-approval',
                                kwargs={'key': user.space_request_key, 'action': 'reject'}))
                }

                subject = "Is %s %s a member of %s?" % (user.first_name, user.last_name, user.space.name)
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
                to = user.space_approver
                message = htmly.render(d)
                try:
                    msg = EmailMessage(subject, message, to=[to], from_email=from_email)
                    msg.content_subtype = 'html'
                    msg.send()
                except Exception as e:
                    # TODO: oh dear - how should we handle this gracefully?!?
                    print("Error sending email" + str(e))

        # commit changes to the DB
        return super(CustomUserCreationForm, self).save(commit)


class SupporterMembershipForm(ModelForm):
    class Meta:
        model = SupporterMembership
        fields = ('fee', 'statement')
        widgets = {
            'fee': forms.NumberInput(attrs={'step':0.25})
        }

    # ensure fee is not less than £10.00
    def clean_fee(self):
        data = self.cleaned_data['fee']
        if data < 10:
            raise forms.ValidationError("Minimum £10.00")
        return data

    # ensure statement is not empty
    def clean_statement(self):
        data = self.cleaned_data['statement']
        if data == "":
            raise forms.ValidationError("Please write at least a few words :)")
        return data


class NewSpaceForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    main_website_url = forms.URLField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=True)
    have_premises = forms.BooleanField(required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    lat = forms.DecimalField(max_digits=10, decimal_places=7, initial=54.1)
    lng = forms.DecimalField(max_digits=10, decimal_places=7, initial=-2.1)
