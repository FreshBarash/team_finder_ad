import re
from urllib.parse import urlparse
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import User

PHONE_RE = re.compile(r"^(?:8|\+7)\d{10}$")


def normalize_phone(phone):
    """Приводит 8XXXXXXXXXX и +7XXXXXXXXXX к единому виду +7XXXXXXXXXX."""
    phone = phone.strip().replace(" ", "")
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    return phone


def validate_github(url):
    if not url:
        return url
    host = (urlparse(url).netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "github.com":
        raise forms.ValidationError("Ссылка должна вести на github.com")
    return url


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        labels = {"name": "Имя", "surname": "Фамилия", "email": "Email"}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {"avatar": forms.FileInput()}

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone
        phone = normalize_phone(phone)
        if not PHONE_RE.match(phone):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )
        qs = User.objects.filter(phone=phone).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Этот номер телефона уже используется")
        return phone

    def clean_github_url(self):
        return validate_github(self.cleaned_data.get("github_url", ""))


class ChangePasswordForm(PasswordChangeForm):
    """old_password, new_password1, new_password2 — как ожидает шаблон."""
    pass
