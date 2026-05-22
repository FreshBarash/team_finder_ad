from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("favorites/", views.favorite_projects, name="favorites"),
    path("create-project/", views.create_project, name="create"),
    path("skills/", views.skill_autocomplete, name="skill-autocomplete"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_project, name="edit"),
    path("<int:pk>/toggle-favorite/", views.toggle_favorite, name="toggle-favorite"),
    path("<int:pk>/toggle-participate/", views.toggle_participate, name="toggle-participate"),
    path("<int:pk>/complete/", views.complete_project, name="complete"),
    path("<int:pk>/skills/add/", views.add_skill, name="skill-add"),
    path("<int:pk>/skills/<int:skill_id>/remove/", views.remove_skill, name="skill-remove"),
]
