from django.conf import settings
from django.db import models

SKILL_NAME_MAX_LENGTH = 124
PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_OPEN = "Open"
ANOTHER_PROJECT_STATUS_OPEN = "open"
PROJECT_STATUS_CLOSE = "Closed"
ANOTHER_PROJECT_STATUS_CLOSE = "closed"
PROJECT_STATUS_MAX_LENGTH = 6

class Skill(models.Model):
    name = models.CharField("Название", max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        PROJECT_STATUS_OPEN,
        ANOTHER_PROJECT_STATUS_OPEN,
        PROJECT_STATUS_CLOSE,
        ANOTHER_PROJECT_STATUS_CLOSE,
    ]

    name = models.CharField("Название", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField("Описание", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    github_url = models.URLField("GitHub", blank=True)
    status = models.CharField(
        "Статус", max_length=PROJECT_STATUS_MAX_LENGTH, choices=STATUS_CHOICES, default="open"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )
    skills = models.ManyToManyField(
        Skill, related_name="projects", blank=True, verbose_name="Необходимые навыки"
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
