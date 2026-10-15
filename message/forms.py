from django import forms
from .models import Conversation
from django.core.exceptions import ValidationError


class GroupForm(forms.ModelForm):
    class Meta:
        model = Conversation
        fields = ["participants", "admin", "group_name", "group_image"]

    def clean(self):
        cleaned = super().clean()
        participants = cleaned.get("participants")
        admins = cleaned.get("admin")

        if participants and participants.count() < 2:
            raise ValidationError("A group needs at least 3 Members.")
        if admins.count() == 0:
            raise ValidationError("A group needs at least 1 Admin.")
        return cleaned
