from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_pro")
    list_filter = ("is_pro",)
    search_fields = ("user__username", "user__email")


