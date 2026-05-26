import io, random, uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

from .managers import UserManager
from .utils import AVATAR_FONT_SIZE, generate_avatar

AVATAR_COLOR_GREY_BLUE = "#4F6D7A"
AVATAR_COLOR_GREY = "#6C7A89"
AVATAR_COLOR_DARK_GREY = "#5D5C61"
AVATAR_COLOR_LIGHT_DARK_BLUE = "#7395AE"
AVATAR_COLOR_MOUSE = "#557A95"
AVATAR_COLOR_LIGHT_BROWN = "#8E7C68"
AVATAR_COLOR_BLEACH_PINK = "#A26769"
AVATAR_COLOR_VIOLET = "#6B5B95"
AVATAR_COLOR_GREY_GREEN = "#5B7065"
AVATAR_COLOR_LIGHT_GREY_BROWN = "#92857A"
AVATAR_COLOR_BLUE_GREEN = "#3C6E71"
AVATAR_COLOR_DARK_VIOLET = "#704C5E"
AVATAR_COLOR_CAT_TOM = "#4A5859"
AVATAR_COLOR_LIGHT_GREY = "#6A7B76"
AVATAR_COLOR_BLEACH_VIOLET = "#7D6B7D"

AVATAR_COLORS = [
    AVATAR_COLOR_DARK_SLATE,
    AVATAR_COLOR_SLATE_GRAY,
    AVATAR_COLOR_DIM_GRAY,
    AVATAR_COLOR_STEEL_BLUE,
    AVATAR_COLOR_MUTED_BLUE,
    AVATAR_COLOR_WARM_GRAY,
    AVATAR_COLOR_BURGUNDY,
    AVATAR_COLOR_PURPLE,
    AVATAR_COLOR_FOREST,
    AVATAR_COLOR_DUSTY_ROSE,
    AVATAR_COLOR_TEAL,
    AVATAR_COLOR_MAUVE,
    AVATAR_COLOR_DARK_OLIVE,
    AVATAR_COLOR_MUTED_TEAL,
    AVATAR_COLOR_LAVENDER,
]

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField("Телефон", max_length=12, blank=True)
    github_url = models.URLField("GitHub", blank=True)
    about = models.TextField("О себе", max_length=256, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Администратор", default=False)

    skills = models.ManyToManyField(
        "projects.Skill", related_name="users", blank=True, verbose_name="Навыки"
    )
    favorites = models.ManyToManyField(
        "projects.Project", related_name="interested_users", blank=True,
        verbose_name="Избранные проекты",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            generate_avatar(self)
        super().save(*args, **kwargs)
