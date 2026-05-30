from django.test import TestCase
from django.urls import reverse
from projects.models import Project, Skill

from .models import User

TEST_EMAIL_ANNA = "a@example.com"
TEST_EMAIL_S = "s@example.com"
TEST_EMAIL_TEST = "t@example.com"
TEST_EMAIL_USER = "u@example.com"
TEST_EMAIL_O = "o@example.com"
TEST_EMAIL_ME = "me@example.com"

TEST_NAME_ANNA = "Анна"
TEST_SURNAME_ANNA = "Иванова"
TEST_NAME_S = "С"
TEST_SURNAME_S = "С"
TEST_NAME_TEST = "Тест"
TEST_SURNAME_TEST = "Тестов"
TEST_SURNAME_T = "T"
TEST_NAME_U = "Ю"
TEST_SURNAME_U = "Ю"
TEST_NAME_O = "О"
TEST_SURNAME_O = "О"
TEST_NAME_ME = "Я"
TEST_SURNAME_ME = "Я"

TEST_PASSWORD_EXAMPLE = "pass12345"
TEST_PASSWORD = "Secret123!"
TEST_PASSWORD_BAD = "bad"

TEST_PHONE_VALID = "89001234567"
TEST_PHONE_NORMALIZED = "+79001234567"
TEST_PHONE_INVALID = "123"

TEST_GITHUB_URL_VALID = ""
TEST_GITHUB_URL_INVALID = "https://gitlab.com/x"

TEST_SKILL_PYTHON = "Python"
TEST_SKILL_GO = "Go"

TEST_PROJECT_NAME = "Мой"

ERROR_WRONG_CREDENTIALS = "Неверный email или пароль"
ERROR_PHONE_FORMAT = "формате"
ERROR_GITHUB_DOMAIN = "github.com"

REDIRECT_PROJECTS_LIST = "/projects/list/"

STATUS_OK = "ok"
STATUS_ADDED_TRUE = True
STATUS_ADDED_KEY = "added"
STATUS_STATUS_KEY = "status"
SKILL_ID_KEY = "skill_id"

class UserModelTests(TestCase):
    def test_avatar_generated_on_create(self):
        user = User.objects.create_user(TEST_EMAIL_ANNA, TEST_NAME_ANNA, TEST_SURNAME_ANNA, TEST_PASSWORD_EXAMPLE)
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_superuser_flags(self):
        admin = User.objects.create_superuser(TEST_EMAIL_S, TEST_NAME_S, TEST_SURNAME_S, TEST_PASSWORD_EXAMPLE)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthFlowTests(TestCase):
    def test_register_creates_and_logs_in(self):
        resp = self.client.post(
            reverse("users:register"),
            {"name": TEST_NAME_TEST, "surname": TEST_SURNAME_TEST, "email": TEST_EMAIL_TEST, "password": TEST_PASSWORD},
        )
        self.assertRedirects(resp, REDIRECT_PROJECTS_LIST)
        self.assertTrue(User.objects.filter(email=TEST_EMAIL_TEST).exists())

    def test_login_wrong_password_shows_error(self):
        User.objects.create_user(TEST_EMAIL_TEST, TEST_NAME_TEST, TEST_SURNAME_T, TEST_PASSWORD)
        resp = self.client.post(reverse("users:login"), {"email": TEST_EMAIL_TEST,, "password": TEST_PASSWORD_BAD})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, ERROR_WRONG_CREDENTIALS)

    def test_logout_redirects_home(self):
        User.objects.create_user(TEST_EMAIL_TEST, TEST_NAME_TEST, TEST_SURNAME_T, TEST_PASSWORD)
        self.client.login(username=TEST_EMAIL_TEST, password=TEST_PASSWORD)
        self.assertRedirects(self.client.get(reverse("users:logout")), REDIRECT_PROJECTS_LIST)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(TEST_EMAIL_USER, TEST_NAME_U, TEST_SURNAME_U, TEST_PASSWORD)
        self.client.force_login(self.user)

    def test_phone_normalized_and_validated(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": TEST_NAME_U, "surname": TEST_SURNAME_U, "phone": TEST_PHONE_VALID, "about": "", "github_url": TEST_GITHUB_URL_VALID},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, TEST_PHONE_NORMALIZED)
        self.assertEqual(resp.status_code, 302)

    def test_bad_phone_rejected(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": TEST_NAME_U, "surname": TEST_SURNAME_U, "phone": TEST_PHONE_INVALID, "about": "", "github_url": TEST_GITHUB_URL_VALID},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, ERROR_PHONE_FORMAT)

    def test_non_github_url_rejected(self):
        resp = self.client.post(
            reverse("users:edit-profile"),
            {"name": TEST_NAME_U, "surname": TEST_SURNAME_U, "phone": "", "about": "", "github_url": TEST_GITHUB_URL_INVALID},
        )
        self.assertContains(resp, ERROR_GITHUB_DOMAIN)


class UserSkillTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(TEST_EMAIL_USER, TEST_NAME_U, TEST_SURNAME_U, TEST_PASSWORD)
        self.client.force_login(self.user)

    def test_add_and_remove_skill(self):
        resp = self.client.post(
            reverse("users:skill-add", args=[self.user.id]),
            data='{"name":"Python"}', content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data[STATUS_ADDED_KEY])
        self.assertTrue(self.user.skills.filter(name="Python").exists())

        resp = self.client.post(reverse("users:skill-remove", args=[self.user.id, data[SKILL_ID_KEY]]))
        self.assertEqual(resp.json()[STATUS_STATUS_KEY], STATUS_OK)
        self.assertFalse(self.user.skills.exists())

    def test_cannot_edit_other_users_skills(self):
        other = User.objects.create_user(TEST_EMAIL_O, TEST_NAME_O, TEST_SURNAME_O, TEST_PASSWORD)
        resp = self.client.post(
            reverse("users:skill-add", args=[other.id]),
            data='{"name":"Python"}', content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)


class UserListFilterTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user(TEST_EMAIL_ME, TEST_NAME_ME, TEST_SURNAME_ME, TEST_PASSWORD)
        self.other = User.objects.create_user(TEST_EMAIL_O, TEST_NAME_O, TEST_SURNAME_O, TEST_PASSWORD)
        self.my_project = Project.objects.create(name=TEST_PROJECT_NAME, owner=self.me)
        self.client.force_login(self.me)

    def test_participants_of_my_projects(self):
        self.my_project.participants.add(self.other)
        resp = self.client.get(reverse("users:list"), {"filter": "participants-of-my-projects"})
        self.assertIn(self.other, resp.context["participants"])

    def test_skill_filter(self):
        skill = Skill.objects.create(name=TEST_SKILL_GO)
        self.other.skills.add(skill)
        resp = self.client.get(reverse("users:list"), {"skill": TEST_SKILL_GO})
        self.assertEqual(list(resp.context["participants"]), [self.other])
