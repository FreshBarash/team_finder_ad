from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, UserCreationForm

from .models import User


class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "surname")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    change_password_form = AdminPasswordChangeForm
    ordering = ["id"]
    list_display = ["id", "email", "name", "surname", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "name", "surname"]
    filter_horizontal = ["skills", "favorites", "groups", "user_permissions"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личные данные", {"fields": ("name", "surname", "avatar", "about", "phone", "github_url")}),
        ("Навыки и избранное", {"fields": ("skills", "favorites")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "surname", "password1", "password2"),
        }),
    )
