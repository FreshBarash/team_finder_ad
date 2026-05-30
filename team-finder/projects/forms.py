from urllib.parse import urlparse

from django import forms

from .models import Project
from ..users.utils import validate_github


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус",
        choices=[("open", "Открыт"), ("closed", "Закрыт")],
        widget=forms.Select,
    )

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
        }

    def clean_github_url(self):
        return validate_github(self.cleaned_data.get("github_url", ""))
