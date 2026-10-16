import os
from django import forms
from .models import Conversation, Message, MessageAttachment
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
        if admins and admins.count() == 0:
            raise ValidationError("A group needs at least 1 Admin. ")
        return cleaned


class MessageForm(forms.Form):
    content = forms.CharField(required=False)
    file = forms.FileField(required=False)

    ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".webm"]
    ALLOWED_PDF_EXTENSIONS = [".pdf"]

    ALLOWED_EXTENSIONS = (
        ALLOWED_IMAGE_EXTENSIONS + ALLOWED_VIDEO_EXTENSIONS + ALLOWED_PDF_EXTENSIONS
    )
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_VIDEO_SIZE = 50 * 1024 * 1024
    MAX_PDF_SIZE = 10 * 1024 * 1024

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get("content")
        file = cleaned_data.get("file")

        if not content and not file:
            raise ValidationError("Provide a message or attach a file.")

        if file:
            self._validate_file(file)

        return cleaned_data

    def _validate_file(self, file):

        ext = os.path.splitext(file.name)[1].lower()

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type '{ext}'. " f"Allowed: images, videos, and PDF."
            )

        content_type = getattr(file, "content_type", "") or ""
        valid_mime = (
            content_type.startswith("image/")
            or content_type.startswith("video/")
            or content_type == "application/pdf"
        )

        if content_type and not valid_mime:
            raise ValidationError(
                "Invalid MIME type. Only image, video, or PDF allowed."
            )

        if ext in self.ALLOWED_IMAGE_EXTENSIONS and file.size > self.MAX_IMAGE_SIZE:
            raise ValidationError(
                f"Image too large. Max {self.MAX_IMAGE_SIZE // (1024 * 1024)} MB."
            )
        if ext in self.ALLOWED_VIDEO_EXTENSIONS and file.size > self.MAX_VIDEO_SIZE:
            raise ValidationError(
                f"Video too large. Max {self.MAX_VIDEO_SIZE // (1024 * 1024)} MB."
            )
        if ext in self.ALLOWED_PDF_EXTENSIONS and file.size > self.MAX_PDF_SIZE:
            raise ValidationError(
                f"PDF too large. Max {self.MAX_PDF_SIZE // (1024 * 1024)} MB."
            )

    def save(self, user, conversation):
        content = self.cleaned_data.get("content", "").strip()
        file = self.cleaned_data.get("file")

        message = Message.objects.create(content=content, sender=user, conversation=conversation)

        if file:
            content_type = getattr(file, "content_type")
            file_type = content_type.split("/")[0] if "/" in content_type else "unknown"

            MessageAttachment.objects.create(
                file_name=file.name,
                file_type=file_type,
                file=file,
                message=message,
            )

        return message
