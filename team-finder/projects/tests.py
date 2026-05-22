from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import Project, Skill


class ProjectListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u@example.com", "Ю", "Ю", "Secret123!")

    def test_root_redirects_to_project_list(self):
        self.assertRedirects(self.client.get("/"), "/projects/list/")

    def test_ordered_newest_first_and_paginated(self):
        for i in range(15):
            Project.objects.create(name=f"P{i}", owner=self.user)
        resp = self.client.get(reverse("projects:list"))
        self.assertEqual(len(resp.context["projects"]), 12)
        names = [p.name for p in resp.context["projects"]]
        self.assertEqual(names[0], "P14")

    def test_skill_filter(self):
        skill = Skill.objects.create(name="Django")
        p = Project.objects.create(name="WithSkill", owner=self.user)
        p.skills.add(skill)
        Project.objects.create(name="NoSkill", owner=self.user)
        resp = self.client.get(reverse("projects:list"), {"skill": "Django"})
        self.assertEqual(list(resp.context["projects"]), [p])


class ProjectCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u@example.com", "Ю", "Ю", "Secret123!")
        self.client.force_login(self.user)

    def test_create_sets_owner_and_participant(self):
        resp = self.client.post(
            reverse("projects:create"),
            {"name": "Новый", "description": "d", "github_url": "", "status": "open"},
        )
        project = Project.objects.get(name="Новый")
        self.assertRedirects(resp, f"/projects/{project.id}/")
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_non_github_url_rejected(self):
        resp = self.client.post(
            reverse("projects:create"),
            {"name": "X", "description": "", "github_url": "https://gitlab.com/x", "status": "open"},
        )
        self.assertContains(resp, "github.com")

    def test_only_owner_can_edit(self):
        other = User.objects.create_user("o@example.com", "О", "О", "Secret123!")
        project = Project.objects.create(name="Чужой", owner=other)
        resp = self.client.get(reverse("projects:edit", args=[project.id]))
        self.assertEqual(resp.status_code, 302)


class ProjectActionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@example.com", "О", "О", "Secret123!")
        self.user = User.objects.create_user("u@example.com", "Ю", "Ю", "Secret123!")
        self.project = Project.objects.create(name="P", owner=self.owner)
        self.client.force_login(self.user)

    def test_toggle_favorite(self):
        url = reverse("projects:toggle-favorite", args=[self.project.id])
        self.assertTrue(self.client.post(url).json()["favorited"])
        self.assertFalse(self.client.post(url).json()["favorited"])

    def test_toggle_participate(self):
        url = reverse("projects:toggle-participate", args=[self.project.id])
        self.assertTrue(self.client.post(url).json()["participant"])
        self.assertIn(self.user, self.project.participants.all())

    def test_favorite_requires_login(self):
        self.client.logout()
        resp = self.client.post(reverse("projects:toggle-favorite", args=[self.project.id]))
        self.assertEqual(resp.status_code, 302)

    def test_complete_only_owner(self):
        resp = self.client.post(reverse("projects:complete", args=[self.project.id]))
        self.assertEqual(resp.status_code, 403)

    def test_complete_by_owner(self):
        self.client.force_login(self.owner)
        resp = self.client.post(reverse("projects:complete", args=[self.project.id]))
        self.assertEqual(resp.json()["project_status"], "closed")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")


class ProjectSkillTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@example.com", "О", "О", "Secret123!")
        self.project = Project.objects.create(name="P", owner=self.owner)
        self.client.force_login(self.owner)

    def test_autocomplete_limits_and_orders(self):
        for n in ["Django", "Docker", "Dart", "Go"]:
            Skill.objects.create(name=n)
        resp = self.client.get(reverse("projects:skill-autocomplete"), {"q": "D"})
        names = [s["name"] for s in resp.json()]
        self.assertEqual(names, ["Dart", "Django", "Docker"])

    def test_add_creates_new_skill(self):
        resp = self.client.post(
            reverse("projects:skill-add", args=[self.project.id]),
            data='{"name":"Rust"}', content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["created"])
        self.assertTrue(data["added"])
        self.assertIn("skill_id", data)
        self.assertIn("name", data)

    def test_add_existing_again_not_added(self):
        skill = Skill.objects.create(name="Rust")
        self.project.skills.add(skill)
        resp = self.client.post(
            reverse("projects:skill-add", args=[self.project.id]),
            data=f'{{"skill_id":{skill.id}}}', content_type="application/json",
        )
        self.assertFalse(resp.json()["added"])

    def test_remove_skill_keeps_it_in_db(self):
        skill = Skill.objects.create(name="Rust")
        self.project.skills.add(skill)
        resp = self.client.post(reverse("projects:skill-remove", args=[self.project.id, skill.id]))
        self.assertEqual(resp.json()["status"], "ok")
        self.assertFalse(self.project.skills.exists())
        self.assertTrue(Skill.objects.filter(name="Rust").exists())
