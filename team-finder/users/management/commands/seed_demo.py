from django.core.management.base import BaseCommand

from projects.models import Project, Skill
from users.models import User

DEMO_PASSWORD = "TeamFinder123"

USERS = [
    ("anna@example.com", "Анна", "Иванова", "+79001112233", "Frontend-разработчик, люблю React."),
    ("boris@example.com", "Борис", "Петров", "+79002223344", "Backend на Django, ищу команду."),
    ("vera@example.com", "Вера", "Сидорова", "+79003334455", "UX/UI дизайнер."),
    ("grigory@example.com", "Григорий", "Кузнецов", "+79004445566", "DevOps и немного бэкенда."),
]

PROJECTS = [
    ("Маркетплейс хобби", "Платформа для обмена хобби-услугами между людьми.", ["Django", "React", "PostgreSQL"]),
    ("Трекер привычек", "Мобильное приложение для отслеживания привычек.", ["Flutter", "Firebase"]),
    ("Агрегатор рецептов", "Сервис подбора рецептов по имеющимся продуктам.", ["Python", "FastAPI", "React"]),
    ("Доска объявлений", "Локальная доска объявлений для соседей.", ["Django", "PostgreSQL"]),
    ("Планировщик встреч", "Удобный подбор общего времени для встреч.", ["Vue", "Node.js"]),
]


class Command(BaseCommand):
    help = "Создаёт суперпользователя и демонстрационные данные (пользователи, проекты, навыки)."

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={"name": "Админ", "surname": "Главный", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Создан суперпользователь admin@example.com / admin12345"))

        users = [admin]
        for email, name, surname, phone, about in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": name, "surname": surname, "phone": phone, "about": about},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users.append(user)

        for i, (pname, desc, skills) in enumerate(PROJECTS):
            owner = users[(i % (len(users) - 1)) + 1]
            project, created = Project.objects.get_or_create(
                name=pname, owner=owner, defaults={"description": desc}
            )
            if created:
                project.participants.add(owner)
                for skill_name in skills:
                    skill, _ = Skill.objects.get_or_create(name=skill_name)
                    project.skills.add(skill)

        self.stdout.write(self.style.SUCCESS(
            f"Готово. Пользователей: {User.objects.count()}, проектов: {Project.objects.count()}, "
            f"навыков: {Skill.objects.count()}. Пароль обычных пользователей: {DEMO_PASSWORD}"
        ))
