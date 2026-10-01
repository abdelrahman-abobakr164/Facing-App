from django import forms
from django.contrib.auth import get_user_model

from accounts.models import Contact

User = get_user_model()


class SettingsForm(forms.ModelForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username...",
            }
        ),
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name...",
            }
        ),
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name...",
            }
        ),
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Bio...",
            }
        ),
    )

    city = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "City...",
            }
        ),
    )
    place = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Location...",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "img",
            "bio",
            "city",
            "place",
            "is_private",
            "show_followers",
            "show_following",
            "check_follower",
        ]


class ContactForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "style2-input ps-5 form-control text-grey-900 font-xsss fw-600",
                "placeholder": "Your Email Address...",
            }
        ),
    )

    class Meta:
        model = Contact
        fields = ["email", "message"]
