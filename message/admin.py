from django.contrib import admin
from .models import *


class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "content", "read"]
    list_editable = ("read",)
    list_per_page = 20


admin.site.register(Message, MessageAdmin)
admin.site.register(MessageAttachment)
admin.site.register(Conversation)
