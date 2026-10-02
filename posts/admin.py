from django.contrib import admin
from .models import *


admin.site.register(Post)
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "body", "created_at", "updated_at"]
    list_per_page = 20
    search_fields = ["user", "post"]


admin.site.register(PostLike)
admin.site.register(CommentLike)
admin.site.register(PostMedia)
