from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("list/", views.user_list, name="list"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("edit-profile/", views.edit_profile, name="edit-profile"),
    path("change-password/", views.change_password, name="change-password"),
    path("skills/", views.skill_autocomplete, name="skill-autocomplete"),
    path("<int:pk>/", views.user_detail, name="detail"),
    path("<int:pk>/skills/add/", views.add_skill, name="skill-add"),
    path("<int:pk>/skills/<int:skill_id>/remove/", views.remove_skill, name="skill-remove"),
]
