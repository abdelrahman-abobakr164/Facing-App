from django.contrib import admin
from .models import *

admin.site.register(Story)
admin.site.register(StoryLike)
admin.site.register(StoryView)
