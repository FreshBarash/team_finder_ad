import re

from urllib.parse import urlparse
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .models import User
from .utils import normalize_phone, validate_github, PHONE_RE, clean_phone


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


    def clean_github_url(self):
        return validate_github(self.cleaned_data.get("github_url", ""))
