from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ("is_pro", "email_verified", "admin_approved", "admin_notes")
    readonly_fields = ("email_verified",)


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "email_verified_status",
        "admin_approved_status",
        "date_joined",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "profile__email_verified",
        "profile__admin_approved",
    )
    
    def email_verified_status(self, obj):
        if hasattr(obj, "profile"):
            if obj.profile.email_verified:
                return format_html('<span style="color: green;">✓ Подтвержден</span>')
            else:
                return format_html('<span style="color: red;">✗ Не подтвержден</span>')
        return "—"
    email_verified_status.short_description = "Email статус"
    
    def admin_approved_status(self, obj):
        if hasattr(obj, "profile"):
            if obj.profile.admin_approved:
                return format_html('<span style="color: green;">✓ Одобрен</span>')
            else:
                return format_html('<span style="color: orange;">⏳ Ожидает</span>')
        return "—"
    admin_approved_status.short_description = "Модерация"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "email_verified",
        "admin_approved",
        "is_pro",
        "user_email",
    )
    list_filter = ("is_pro", "email_verified", "admin_approved")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("email_verification_token",)
    fields = (
        "user",
        "is_pro",
        "email_verified",
        "email_verification_token",
        "admin_approved",
        "admin_notes",
    )
    actions = ["approve_users", "reject_users"]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"
    
    def approve_users(self, request, queryset):
        """Одобрить выбранных пользователей."""
        count = queryset.update(admin_approved=True)
        self.message_user(
            request,
            f"Одобрено пользователей: {count}",
        )
    approve_users.short_description = "Одобрить выбранных пользователей"
    
    def reject_users(self, request, queryset):
        """Отклонить выбранных пользователей."""
        count = queryset.update(admin_approved=False)
        self.message_user(
            request,
            f"Отклонено пользователей: {count}",
        )
    reject_users.short_description = "Отклонить выбранных пользователей"


