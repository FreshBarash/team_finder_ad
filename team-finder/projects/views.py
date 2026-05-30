import json

from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project, Skill

PER_PAGE = 12
SKILL_FILTER_NUMBER = 10


def _parse_body(request):
    """Возвращает dict из JSON-тела или из POST-формы."""
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or b"{}")
        except (ValueError, TypeError):
            return {}
    return request.POST


def project_list(request):
    projects = Project.objects.select_related("owner").all()

    active_skill = request.GET.get("skill")
    if active_skill:
        projects = projects.filter(skills__name=active_skill).distinct()

    paginator = Paginator(projects, PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    all_skills = Skill.objects.values_list("name", flat=True)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj,
            "page_obj": page_obj,
            "all_skills": all_skills,
            "active_skill": active_skill,
        },
    )


@login_required
def favorite_projects(request):
    projects = request.user.favorites.select_related("owner").all()
    return render(request, "projects/favorite_projects.html", {"projects": projects})


def project_detail(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id:
        return redirect("projects:detail", pk=project.pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
@require_POST
def toggle_favorite(request, pk):
   
    project = Project.objects.filter(pk=pk).first()

    if project is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Project not found",
            },
            status=HTTPStatus.NOT_FOUND,
        )
    
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)
        
    favorited = request.user.favorites.filter(pk=project.pk).exists()
    
    return JsonResponse({"status": "ok", "favorited": favorited})


@login_required
@require_POST
def toggle_participate(request, pk):
    
    project = Project.objects.filter(pk=pk).first()

    if project is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Project not found",
            },
            status=HTTPStatus.NOT_FOUND,
        ))
    
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    participant = project.participants.filter(pk=request.user.pk).exists():
    
    return JsonResponse({"status": "ok", "participant": participant})


@login_required
@require_POST
def complete_project(request, pk):
    
    project = Project.objects.filter(pk=pk).first()

    if project is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Project not found",
            },
            status=HTTPStatus.NOT_FOUND,
        )
    
    if project.owner_id != request.user.id or project.status != "open":
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


def skill_autocomplete(request):
    autoskill = request.GET.get("q", "")
    skills = Skill.objects.filter(name__istartswith=q).order_by("name")[:SKILL_FILTER_NUMBER]
    return JsonResponse(list(skills.values("id", "name")), safe=False)


@login_required
@require_POST
def add_skill(request, pk):
    
    project = Project.objects.filter(pk=pk).first()

    if project is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Project not found",
            },
            status=HTTPStatus.NOT_FOUND,
        )
    
    if project.owner_id != request.user.id:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    data = _parse_body(request)
    skill_id = data.get("skill_id")
    name = (data.get("name") or "").strip()

    created = False
    if skill_id:
        
        skill = Skill.objects.filter(pk=skill_id).first()

        if skill is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Skill not found",
                },
                status=HTTPStatus.NOT_FOUND,
            )
        
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)

    added = False
    if not project.skills.filter(pk=skill.pk).exists():
        project.skills.add(skill)
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
    
    project = Project.objects.filter(pk=pk).first()

    if project is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Project not found",
            },
            status=HTTPStatus.NOT_FOUND,
        )
    
    if project.owner_id != request.user.id:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    
    skill = Skill.objects.filter(pk=skill_id).first()

    if skill is None:
        return JsonResponse(
            {
                "status": "error",
                "message": "Skill not found",
            },
            status=HTTPStatus.NOT_FOUND,
        )
    
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "error"}, status=HTTPStatus.NOT_FOUND)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
