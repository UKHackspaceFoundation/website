from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(ModelForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email','first_name','last_name','space',)

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # override User model to ensure first and last names are required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
