from django.test import TestCase
from django.urls import reverse
from projects.models import Project, Skill

from .models import User


class UserModelTests(TestCase):
    def test_avatar_generated_on_create(self):
        user = User.objects.create_user("a@example.com", "Анна", "Иванова", "pass12345")
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_superuser_flags(self):
        admin = User.objects.create_superuser("s@example.com", "С", "С", "pass12345")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthFlowTests(TestCase):
    def test_register_creates_and_logs_in(self):
        resp = self.client.post(
            reverse("users:register"),
            {"name": "Тест", "surname": "Тестов", "email": "t@example.com", "password": "Secret123!"},
        )
        self.assertRedirects(resp, "/projects/list/")
        self.assertTrue(User.objects.filter(email="t@example.com").exists())

    def test_login_wrong_password_shows_error(self):
        User.objects.create_user("t@example.com", "Т", "Т", "Secret123!")
        resp = self.client.post(reverse("users:login"), {"email": "t@example.com", "password": "bad"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Неверный email или пароль")

    def test_logout_redirects_home(self):
        User.objects.create_user("t@example.com", "Т", "Т", "Secret123!")
        self.client.login(username="t@example.com", password="Secret123!")
        self.assertRedirects(self.client.get(reverse("users:logout")), "/projects/list/")


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u@example.com", "Ю", "Ю", "Secret123!")
        self.client.force_login(self.user)

    def test_phone_normalized_and_validated(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": "Ю", "surname": "Ю", "phone": "89001234567", "about": "", "github_url": ""},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79001234567")
        self.assertEqual(resp.status_code, 302)

    def test_bad_phone_rejected(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": "Ю", "surname": "Ю", "phone": "123", "about": "", "github_url": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "формате")

    def test_non_github_url_rejected(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": "Ю", "surname": "Ю", "phone": "", "about": "", "github_url": "https://gitlab.com/x"},
        )
        self.assertContains(resp, "github.com")


class UserSkillTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u@example.com", "Ю", "Ю", "Secret123!")
        self.client.force_login(self.user)

    def test_add_and_remove_skill(self):
        resp = self.client.post(
            reverse("users:skill-add", args=[self.user.id]),
            data='{"name":"Python"}', content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["added"])
        self.assertTrue(self.user.skills.filter(name="Python").exists())

        resp = self.client.post(reverse("users:skill-remove", args=[self.user.id, data["skill_id"]]))
        self.assertEqual(resp.json()["status"], "ok")
        self.assertFalse(self.user.skills.exists())

    def test_cannot_edit_other_users_skills(self):
        other = User.objects.create_user("o@example.com", "О", "О", "Secret123!")
        resp = self.client.post(
            reverse("users:skill-add", args=[other.id]),
            data='{"name":"Python"}', content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)


class UserListFilterTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user("me@example.com", "Я", "Я", "Secret123!")
        self.other = User.objects.create_user("o@example.com", "О", "О", "Secret123!")
        self.my_project = Project.objects.create(name="Мой", owner=self.me)
        self.client.force_login(self.me)

    def test_participants_of_my_projects(self):
        self.my_project.participants.add(self.other)
        resp = self.client.get(reverse("users:list"), {"filter": "participants-of-my-projects"})
        self.assertIn(self.other, resp.context["participants"])

    def test_skill_filter(self):
        skill = Skill.objects.create(name="Go")
        self.other.skills.add(skill)
        resp = self.client.get(reverse("users:list"), {"skill": "Go"})
        self.assertEqual(list(resp.context["participants"]), [self.other])
