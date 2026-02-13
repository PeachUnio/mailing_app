from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Создает группу менеджеров'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='Менеджеры')

        permissions = Permission.objects.filter(
            codename__in=[
                'can_view_all_mailings',
                'can_disable_mailing',
                'can_view_all_messages',
                'can_view_all_recipients',
            ]
        )

        group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS(
            f'Группа "Менеджеры" готова с {permissions.count()} правами'
        ))
