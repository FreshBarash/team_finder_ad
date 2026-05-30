import json

from http import HTTPStatus

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.models import Skill

from .forms import LoginForm, ProfileEditForm, RegisterForm
from .models import User

PER_PAGE = 12

OWNERS_OF_FAVOURITE_PROJECTS = lambda u: User.objects.filter(
    owned_projects__in=u.favorites.all()
OWNERS_OF_PARTICIPATING_PROJECTS = lambda u: User.objects.filter(
    owned_projects__participants=u
INTERESTED_IN_MY_PROJECTS = lambda u: User.objects.filter(
    favorites__owner=u
PARTICIPANTS_OF_MY_PROJECTS = lambda u: User.objects.filter(
    participated_projects__owner=u

FILTERS = {
    "owners-of-favorite-projects": OWNERS_OF_FAVOURITE_PROJECTS,
    "owners-of-participating-projects": OWNERS_OF_PARTICIPATING_PROJECTS,
    "interested-in-my-projects": INTERESTED_IN_MY_PROJECTS,
    "participants-of-my-projects": PARTICIPANTS_OF_MY_PROJECTS,
}


def _parse_body(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or b"{}")
        except (ValueError, TypeError):
            return {}
    return request.POST


def user_list(request):
    participants = User.objects.all().order_by("id")

    active_filter = request.GET.get("filter")
    if active_filter and request.user.is_authenticated and active_filter in FILTERS:
        participants = FILTERS[active_filter](request.user).distinct().order_by("id")

    active_skill = request.GET.get("skill")
    if active_skill:
        participants = participants.filter(skills__name=active_skill).distinct()

    paginator = Paginator(participants, PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "all_skills": Skill.objects.values_list("name", flat=True),
            "active_skill": active_skill,
        },
    )


def user_detail(request, pk):
    profile = get_object_or_404(User, pk=pk)
    return render(request, "users/user-details.html", {"user": profile})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:list")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("projects:list")
            form.add_error(None, "Неверный email или пароль")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", pk=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("users:detail", pk=request.user.pk)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})


def skill_autocomplete(request):
    autoskill = request.GET.get("q", "")
    skills = Skill.objects.filter(name__istartswith=q).order_by("name")[:10]
    return JsonResponse(list(skills.values("id", "name")), safe=False)


@login_required
@require_POST
def add_skill(request, pk):
    if request.user.id != pk:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    data = _parse_body(request)
    skill_id = data.get("skill_id")
    name = (data.get("name") or "").strip()

    created = False
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)

    added = False
    if not request.user.skills.filter(pk=skill.pk).exists():
        request.user.skills.add(skill)
        added = True

    return JsonResponse(
        {
            "skill_id": skill.id,
            "id": skill.id,
            "name": skill.name,
            "created": created,
            "added": added,
        }
    )


@login_required
@require_POST
def remove_skill(request, pk, skill_id):
    if request.user.id != pk:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    skill = get_object_or_404(Skill, pk=skill_id)
    if not request.user.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "error"}, status=HTTPStatus.NOT_FOUND)
    request.user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
