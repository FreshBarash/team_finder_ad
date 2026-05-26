import io, random, uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

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


class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError("Пользователь должен иметь email")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")
        return self.create_user(email, name, surname, password, **extra_fields)


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
            self._generate_avatar()
        super().save(*args, **kwargs)

    def _generate_avatar(self):
        size = 256
        bg = random.choice(AVATAR_COLORS)
        image = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(image)
        letter = (self.name[:1] or "?").upper()

        font_path = (
            settings.BASE_DIR / "static" / "fonts"
            / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
        )
        try:
            font = ImageFont.truetype(str(font_path), 130)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        position = ((size - text_w) / 2 - bbox[0], (size - text_h) / 2 - bbox[1])
        draw.text(position, letter, fill="#FFFFFF", font=font)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        filename = f"avatar_{uuid.uuid4()}.png"
        self.avatar.save(filename, ContentFile(buffer.getvalue()), save=False)
