from django.contrib import admin

from .models import Project, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "description"]
    autocomplete_fields = ["owner"]
    filter_horizontal = ["participants", "skills"]
